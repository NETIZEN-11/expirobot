"""
Configuration settings for ExpirioBot.
All configurable parameters are defined here to avoid hardcoding.
"""

import os
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class ArmConfig:
    """Robotic arm configuration."""
    # Servo positions for different arm poses
    positions: Dict[str, List[int]] = field(default_factory=lambda: {
        "front": [90, 75, 0, 30, 90],
        "right": [0, 75, 0, 30, 90],
        "right_top": [0, 75, 0, 60, 90],
        "left_top": [180, 75, 0, 60, 90],
        "left": [180, 75, 0, 30, 90],
        "top": [90, 80, 50, 50, 90],
        "rest": [90, 90, 0, 5, 90],
    })
    
    # Clamp positions
    clamp_open: int = 10
    clamp_close: int = 100
    
    # Movement timing (ms)
    move_time_default: int = 500
    move_time_pickup: int = 1000
    move_time_transition: int = 1000
    move_time_release: int = 500
    
    # Servo timing adjustments
    servo_5_time_factor: float = 1.2
    servo_1_time_factor: float = 0.75


@dataclass
class CameraConfig:
    """Camera configuration."""
    index: int = 0
    width: int = 640
    height: int = 480
    fps: int = 30
    display_width: int = 400
    display_height: int = 300
    queue_maxsize: int = 10
    capture_sleep: float = 0.1


@dataclass
class OCRConfig:
    """OCR configuration."""
    # Tesseract executable path (auto-detected if not set)
    tesseract_cmd: str = ""
    
    # Date regex patterns (tried in order)
    date_patterns: List[str] = field(default_factory=lambda: [
        r'\b\d{2}[./]\d{2}[./]\d{4}\b',  # DD/MM/YYYY or DD.MM.YYYY
        r'\b\d{2}[./]\d{2}[./]\d{2}\b',   # DD/MM/YY or DD.MM.YY
        r'\b\d{4}[./]\d{2}[./]\d{2}\b',   # YYYY/MM/DD or YYYY.MM.DD
    ])
    
    # Preprocessing settings
    threshold_value: int = 128
    threshold_max: int = 255
    threshold_type: int = 0  # cv2.THRESH_BINARY


@dataclass
class GUIConfig:
    """GUI configuration."""
    title: str = "ExpirioBot Control Panel"
    bg_color: str = "#2e2e2e"
    text_color: str = "white"
    accent_color: str = "#4caf50"
    danger_color: str = "#f44336"
    warning_color: str = "yellow"
    font_family: str = "Comfortaa"
    font_size_title: int = 16
    font_size_normal: int = 12
    font_size_large: int = 24
    window_width: int = 700
    window_height: int = 600
    update_interval_ms: int = 10


@dataclass
class ThreadingConfig:
    """Threading configuration."""
    queue_maxsize: int = 10
    capture_sleep: float = 0.1
    producer_daemon: bool = True
    consumer_daemon: bool = True


@dataclass
class Config:
    """Main configuration class."""
    arm: ArmConfig = field(default_factory=ArmConfig)
    camera: CameraConfig = field(default_factory=CameraConfig)
    ocr: OCRConfig = field(default_factory=OCRConfig)
    gui: GUIConfig = field(default_factory=GUIConfig)
    threading: ThreadingConfig = field(default_factory=ThreadingConfig)
    
    # Paths
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    image_save_path: Path = field(default_factory=lambda: Path(__file__).parent.parent / "image.jpg")
    
    # Mode settings
    mock_arm: bool = False
    use_tesseract: bool = True
    
    def __post_init__(self):
        """Auto-detect Tesseract path if not set."""
        if not self.ocr.tesseract_cmd:
            self.ocr.tesseract_cmd = self._find_tesseract()
    
    def _find_tesseract(self) -> str:
        """Auto-detect Tesseract OCR executable path."""
        import platform
        import shutil
        
        # Try system PATH first
        tesseract_path = shutil.which("tesseract")
        if tesseract_path:
            return tesseract_path
        
        # Common Windows paths
        if platform.system() == "Windows":
            common_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                r"C:\Tesseract-OCR\tesseract.exe",
                os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
            ]
            for path in common_paths:
                if os.path.exists(path):
                    return path
        
        # Common Linux/macOS paths
        common_paths = [
            "/usr/bin/tesseract",
            "/usr/local/bin/tesseract",
            "/opt/homebrew/bin/tesseract",
        ]
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        return ""


# Global config instance
config = Config()


def load_config_from_env() -> Config:
    """Load configuration from environment variables."""
    import os
    
    cfg = Config()
    
    # Camera settings
    if cam_idx := os.getenv("EXPIRIOBOT_CAMERA_INDEX"):
        cfg.camera.index = int(cam_idx)
    
    # Tesseract path
    if tess_path := os.getenv("EXPIRIOBOT_TESSERACT_PATH"):
        cfg.ocr.tesseract_cmd = tess_path
    
    # Mock arm mode
    if mock := os.getenv("EXPIRIOBOT_MOCK_ARM"):
        cfg.mock_arm = mock.lower() in ("true", "1", "yes")
    
    # Use Tesseract
    if use_tess := os.getenv("EXPIRIOBOT_USE_TESSERACT"):
        cfg.use_tesseract = use_tess.lower() in ("true", "1", "yes")
    
    # Arm positions from env (JSON format)
    import json
    if arm_positions := os.getenv("EXPIRIOBOT_ARM_POSITIONS"):
        try:
            cfg.arm.positions = json.loads(arm_positions)
        except json.JSONDecodeError:
            pass
    
    return cfg


def get_config() -> Config:
    """Get the global configuration instance."""
    return config