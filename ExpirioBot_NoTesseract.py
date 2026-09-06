#!/usr/bin/env python3
"""
ExpirioBot - Windows Version without Tesseract (Manual Date Entry)
Main entry point for Windows with camera preview and manual date input (mock arm).
"""

import sys
import logging

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


class ExpirioBotNoTesseract:
    """Main application class for Windows version without Tesseract."""
    
    def __init__(self):
        self.config = load_config_from_env()
        self.config.mock_arm = True
        self.config.use_tesseract = False
        
        # Components
        self.arm_controller = None
        self.ocr_processor = None
        self.camera = None
        self.gui = None
        self.date_entry = None
        
        self.running = False
    
    def initialize(self) -> bool:
        """Initialize all components."""
        logger.info("Initializing ExpirioBot (Windows Manual Entry)...")
        
        # Initialize arm controller (mock)
        self.arm_controller = create_arm_controller(mock=True)
        logger.info("Mock arm controller initialized")
        
        # Initialize OCR processor (for date parsing only, no Tesseract needed)
        self.ocr_processor = create_ocr_processor()
        logger.info("OCR processor initialized (date parsing only)")
        
        # Initialize camera
        self.camera = create_camera_manager()
        if not self.camera.start():
            logger.warning("Camera not available - GUI will start but camera preview won't work")
        else:
            logger.info("Camera initialized")
        
        # Initialize GUI
        self.gui = ExpirioBotGUI("ExpirioBot - Manual Date Entry Mode")
        self.gui.setup_video_display()
        self.gui.setup_counters(compact=False)
        self.gui.setup_warning("⚠️ MOCK MODE - Manual Date Entry (No Tesseract Required)")
        
        # Manual input section
        self.date_entry, check_button = self.gui.setup_manual_input("DD/MM/YYYY")
        self.gui.setup_instructions(
            "📝 Enter expiry date in DD/MM/YYYY format (e.g., 25/12/2024)\n"
            "The system will check if it's expired and simulate arm movement"
        )
        
        # Set callbacks
        self.gui.on_manual_check = self.check_manual_date
        
        return True
    
    def check_manual_date(self) -> None:
        """Process manually entered date."""
        if not self.date_entry:
            return
        
        date_str = self.date_entry.get().strip()
        if not date_str or date_str == "DD/MM/YYYY":
            messagebox.showerror("Error", "Please enter a date")
            return
        
        # Process date using OCR processor (for parsing/validation)
        result = self.ocr_processor.process_manual_date(date_str)
        
        if result.success and result.is_expired is not None:
            target = "left" if result.is_expired else "right"
            status = "EXPIRED" if result.is_expired else "VALID"
            emoji = "❌" if result.is_expired else "✅"
            
            message = f"{emoji} {status}! Date: {result.date_string}\nMoving to {target.upper()}"
            logger.info(message)
            
            # Update counters
            if result.is_expired:
                self.gui.increment_expired()
            else:
                self.gui.increment_valid()
            
            # Simulate arm movement
            success = self.arm_controller.pick_and_place(target)
            
            if success:
                messagebox.showinfo("Result", message)
            else:
                messagebox.showerror("Error", "Arm movement simulation failed")
            
            # Clear entry
            self.date_entry.delete(0, 'end')
            self.date_entry.insert(0, "DD/MM/YYYY")
            
        else:
            error_msg = result.error or "Unknown error"
            logger.warning(f"Date processing failed: {error_msg}")
            messagebox.showerror("Error", f"Invalid date: {error_msg}\n\nUse format: DD/MM/YYYY (e.g., 25/12/2024)")
    
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
    print("🤖 ExpirioBot - Manual Date Entry Mode")
    print("=" * 60)
    print("✅ Camera preview (if available)")
    print("✅ GUI ready")
    print("⚠️  No Tesseract required (manual input)")
    print("⚠️  Mock arm mode (no physical hardware)")
    print("=" * 60)
    print("\nEnter dates in format: DD/MM/YYYY")
    print("Example: 25/12/2024 or 25.12.2024\n")
    
    # Import messagebox here to avoid issues if tkinter not available
    global messagebox
    from tkinter import messagebox
    
    app = ExpirioBotNoTesseract()
    app.run()


if __name__ == "__main__":
    main()