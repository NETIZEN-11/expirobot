"""
Camera handling module for ExpirioBot.
Provides unified camera interface for different platforms.
"""

import cv2
import logging
import threading
import queue
import time
from typing import Optional, Tuple, Callable
from dataclasses import dataclass

from .config import get_config, CameraConfig

logger = logging.getLogger(__name__)


@dataclass
class FrameData:
    """Container for frame data."""
    frame: cv2.typing.MatLike
    timestamp: float
    frame_id: int


class CameraManager:
    """Manages camera capture and frame queue."""
    
    def __init__(self, config: Optional[CameraConfig] = None):
        self.config = config or get_config().camera
        self.cap: Optional[cv2.VideoCapture] = None
        self._frame_queue: queue.Queue = queue.Queue(maxsize=self.config.queue_maxsize)
        self._capture_thread: Optional[threading.Thread] = None
        self._running = False
        self._frame_id = 0
        self._lock = threading.Lock()
        self._producer_allowed = threading.Event()
        self._producer_allowed.set()  # Allow by default
    
    def start(self) -> bool:
        """Start camera capture."""
        if self._running:
            logger.warning("Camera already running")
            return True
        
        self.cap = cv2.VideoCapture(self.config.index)
        if not self.cap.isOpened():
            logger.error(f"Cannot open camera index {self.config.index}")
            self.cap = None
            return False
        
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.config.fps)
        
        # Verify camera works
        ret, frame = self.cap.read()
        if not ret:
            logger.error("Camera opened but cannot read frames")
            self.cap.release()
            self.cap = None
            return False
        
        logger.info(f"Camera started: {frame.shape[1]}x{frame.shape[0]}")
        
        self._running = True
        self._frame_id = 0
        self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._capture_thread.start()
        return True
    
    def stop(self) -> None:
        """Stop camera capture."""
        self._running = False
        self._producer_allowed.clear()
        
        if self._capture_thread and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=2.0)
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        # Clear queue
        while not self._frame_queue.empty():
            try:
                self._frame_queue.get_nowait()
            except queue.Empty:
                break
        
        logger.info("Camera stopped")
    
    def _capture_loop(self) -> None:
        """Main capture loop running in separate thread."""
        while self._running:
            self._producer_allowed.wait()
            
            if not self._running:
                break
            
            if self.cap is None:
                time.sleep(0.1)
                continue
            
            ret, frame = self.cap.read()
            if not ret:
                logger.warning("Failed to grab frame")
                time.sleep(0.1)
                continue
            
            with self._lock:
                self._frame_id += 1
                frame_data = FrameData(
                    frame=frame.copy(),
                    timestamp=time.time(),
                    frame_id=self._frame_id
                )
                
                # Handle full queue
                if self._frame_queue.full():
                    try:
                        self._frame_queue.get_nowait()
                    except queue.Empty:
                        pass
                
                self._frame_queue.put(frame_data)
            
            time.sleep(self.config.capture_sleep)
    
    def get_latest_frame(self) -> Optional[FrameData]:
        """Get the latest frame from queue (non-blocking)."""
        try:
            return self._frame_queue.get_nowait()
        except queue.Empty:
            return None
    
    def get_frame_blocking(self, timeout: float = 1.0) -> Optional[FrameData]:
        """Get frame with blocking wait."""
        try:
            return self._frame_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def pause_capture(self) -> None:
        """Pause frame capture."""
        self._producer_allowed.clear()
    
    def resume_capture(self) -> None:
        """Resume frame capture."""
        self._producer_allowed.set()
    
    def is_running(self) -> bool:
        """Check if camera is running."""
        return self._running and self.cap is not None
    
    def get_frame_for_display(self) -> Optional[cv2.typing.MatLike]:
        """Get latest frame resized for display."""
        frame_data = self.get_latest_frame()
        if frame_data is None:
            return None
        
        frame = frame_data.frame
        return cv2.resize(frame, (self.config.display_width, self.config.display_height))
    
    @property
    def queue_size(self) -> int:
        """Get current queue size."""
        return self._frame_queue.qsize()
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def create_camera_manager() -> CameraManager:
    """Factory function to create camera manager."""
    return CameraManager()