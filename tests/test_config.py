"""Tests for ExpirioBot configuration module."""

import pytest
from pathlib import Path
from expiriobot.config import Config, ArmConfig, CameraConfig, OCRConfig, GUIConfig, ThreadingConfig


def test_arm_config_defaults():
    """Test ArmConfig default values."""
    config = ArmConfig()
    
    assert "front" in config.positions
    assert "left" in config.positions
    assert "right" in config.positions
    assert config.clamp_open == 10
    assert config.clamp_close == 100
    assert config.move_time_default == 500


def test_camera_config_defaults():
    """Test CameraConfig default values."""
    config = CameraConfig()
    
    assert config.index == 0
    assert config.width == 640
    assert config.height == 480
    assert config.fps == 30


def test_ocr_config_defaults():
    """Test OCRConfig default values."""
    config = OCRConfig()
    
    assert len(config.date_patterns) > 0
    assert config.threshold_value == 128
    assert r'\d{2}[./]\d{2}[./]\d{4}' in config.date_patterns[0]


def test_gui_config_defaults():
    """Test GUIConfig default values."""
    config = GUIConfig()
    
    assert config.title == "ExpirioBot Control Panel"
    assert config.bg_color == "#2e2e2e"
    assert config.font_family == "Comfortaa"


def test_threading_config_defaults():
    """Test ThreadingConfig default values."""
    config = ThreadingConfig()
    
    assert config.queue_maxsize == 10
    assert config.capture_sleep == 0.1
    assert config.producer_daemon is True
    assert config.consumer_daemon is True


def test_main_config():
    """Test main Config class."""
    config = Config()
    
    assert isinstance(config.arm, ArmConfig)
    assert isinstance(config.camera, CameraConfig)
    assert isinstance(config.ocr, OCRConfig)
    assert isinstance(config.gui, GUIConfig)
    assert isinstance(config.threading, ThreadingConfig)
    assert config.base_dir.exists()
    assert config.image_save_path.name == "image.jpg"