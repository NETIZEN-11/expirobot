#!/usr/bin/env python3
"""
ExpirioBot - Raspberry Pi Version
Main entry point for Raspberry Pi with DOFBOT arm and Tesseract OCR.
"""

import sys
import logging
import threading
import queue
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(__file__))

from expiriobot.config import get_config, load_config_from_env
from expiriobot.arm_control import create_arm_controller
from expiriobot.ocr_processor import create_ocr_processor, OCRResult
from expiriobot.camera import create_camera_manager
from expiriobot.gui import ExpirioBotGUI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExpirioBotPi:
    """Main application class for Raspberry Pi version."""
    
    def __init__(self):
        self.config = load_config_from_env()
        self.config.mock_arm = False
        self.config.use_tesseract = True
        
        # Components
        self.arm_controller = None
        self.ocr_processor = None
        self.camera = None
        self.gui = None
        
        # Threading
        self.processing_event = threading.Event()
        self.processing_event.set()
        self.frame_queue = queue.Queue(maxsize=self.config.threading.queue_maxsize)
        self.consumer_thread = None
        self.running = False
    
    def initialize(self) -> bool:
        """Initialize all components."""
        logger.info("Initializing ExpirioBot (Raspberry Pi)...")
        
        # Initialize arm controller
        try:
            self.arm_controller = create_arm_controller(mock=False)
            logger.info("Arm controller initialized")
        except Exception as e:
            logger.error(f"Failed to initialize arm: {e}")
            return False
        
        # Initialize OCR processor
        self.ocr_processor = create_ocr_processor()
        if not self.ocr_processor.is_available:
            logger.error("OCR not available. Install pytesseract and Tesseract OCR.")
            return False
        logger.info("OCR processor initialized")
        
        # Initialize camera
        self.camera = create_camera_manager()
        if not self.camera.start():
            logger.error("Failed to start camera")
            return False
        logger.info("Camera initialized")
        
        # Initialize GUI
        self.gui = ExpirioBotGUI("ExpirioBot Control Panel - Raspberry Pi")
        self.gui.setup_video_display()
        self.gui.setup_counters()
        self.gui.setup_control_buttons()
        self.gui.setup_warning("Running on Raspberry Pi with DOFBOT")
        
        # Set callbacks
        self.gui.on_start = self.start_processing
        self.gui.on_stop = self.stop_processing
        
        return True
    
    def start_processing(self) -> None:
        """Start frame processing thread."""
        if self.consumer_thread and self.consumer_thread.is_alive():
            logger.warning("Processing already running")
            return
        
        self.processing_event.set()
        self.camera.resume_capture()
        
        self.consumer_thread = threading.Thread(
            target=self._processing_loop,
            daemon=True
        )
        self.consumer_thread.start()
        logger.info("Processing started")
    
    def stop_processing(self) -> None:
        """Stop frame processing."""
        self.processing_event.clear()
        self.camera.pause_capture()
        logger.info("Processing stopped")
    
    def _processing_loop(self) -> None:
        """Main processing loop running in background thread."""
        while self.running:
            self.processing_event.wait()
            
            if not self.running:
                break
            
            frame_data = self.camera.get_frame_blocking(timeout=0.5)
            if frame_data is None:
                continue
            
            # Process frame
            result = self.ocr_processor.process_frame(frame_data.frame)
            
            if result.success and result.is_expired is not None:
                target = "left" if result.is_expired else "right"
                status = "EXPIRED" if result.is_expired else "VALID"
                logger.info(f"Product {status}: {result.date_string} -> {target.upper()}")
                
                # Update counters
                if result.is_expired:
                    self.gui.increment_expired()
                else:
                    self.gui.increment_valid()
                
                # Pause capture during arm movement
                self.camera.pause_capture()
                self.processing_event.clear()
                
                # Move arm
                success = self.arm_controller.pick_and_place(target)
                
                # Resume
                self.camera.resume_capture()
                self.processing_event.set()
                
                if not success:
                    logger.error("Arm movement failed")
            
            elif result.error and result.error != "Date already processed":
                logger.debug(f"OCR: {result.error}")
    
    def update_gui(self) -> None:
        """Update GUI with latest camera frame."""
        frame = self.camera.get_frame_for_display()
        if frame is not None:
            self.gui.update_frame(frame)
    
    def run(self) -> None:
        """Run the application."""
        if not self.initialize():
            logger.error("Initialization failed")
            return
        
        self.running = True
        
        # Start GUI update loop
        self.gui.start_update_loop(self.update_gui)
        
        try:
            self.gui.run()
        finally:
            self.cleanup()
    
    def cleanup(self) -> None:
        """Clean up resources."""
        logger.info("Cleaning up...")
        self.running = False
        self.processing_event.set()  # Unblock processing thread
        self.stop_processing()
        
        if self.camera:
            self.camera.stop()
        
        if self.arm_controller:
            self.arm_controller.cleanup()
        
        if self.gui:
            self.gui.destroy()
        
        logger.info("Cleanup complete")


def main():
    """Main entry point."""
    print("=" * 60)
    print("🤖 ExpirioBot - Raspberry Pi Version")
    print("=" * 60)
    print("Hardware: DOFBOT Arm + Camera")
    print("OCR: Tesseract")
    print("=" * 60)
    
    app = ExpirioBotPi()
    app.run()


if __name__ == "__main__":
    main()