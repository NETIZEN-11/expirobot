"""
OCR processing module for ExpirioBot.
Handles image preprocessing and expiry date extraction.
"""

import cv2
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple
from dataclasses import dataclass
from PIL import Image

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    pytesseract = None

from .config import get_config, OCRConfig

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """Result of OCR processing."""
    success: bool
    date_string: Optional[str] = None
    date_object: Optional[datetime] = None
    is_expired: Optional[bool] = None
    raw_text: str = ""
    error: Optional[str] = None


class OCRProcessor:
    """Handles OCR processing for expiry date detection."""
    
    def __init__(self, config: Optional[OCRConfig] = None):
        self.config = config or get_config().ocr
        self._setup_tesseract()
        self._last_processed_date: Optional[datetime] = None
    
    def _setup_tesseract(self) -> None:
        """Configure Tesseract path if available."""
        if TESSERACT_AVAILABLE and self.config.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self.config.tesseract_cmd
            logger.info(f"Tesseract configured: {self.config.tesseract_cmd}")
        elif TESSERACT_AVAILABLE:
            logger.warning("Tesseract path not configured, using system PATH")
        else:
            logger.warning("pytesseract not installed, OCR unavailable")
    
    def preprocess_image(self, frame) -> cv2.typing.MatLike:
        """
        Preprocess image for better OCR results.
        
        Args:
            frame: OpenCV image frame (BGR)
        
        Returns:
            Preprocessed binary image
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(
            gray,
            self.config.threshold_value,
            self.config.threshold_max,
            self.config.threshold_type
        )
        return binary
    
    def extract_text(self, image_path: Path) -> str:
        """
        Extract text from image using Tesseract OCR.
        
        Args:
            image_path: Path to image file
        
        Returns:
            Extracted text string
        """
        if not TESSERACT_AVAILABLE:
            raise RuntimeError("pytesseract not available")
        
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            logger.debug(f"Extracted text: {text[:200]}...")
            return text
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            raise
    
    def find_date_in_text(self, text: str) -> Optional[str]:
        """
        Find date pattern in extracted text.
        
        Args:
            text: OCR extracted text
        
        Returns:
            Date string if found, None otherwise
        """
        for pattern in self.config.date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None
    
    def parse_date(self, date_string: str) -> Optional[datetime]:
        """
        Parse date string to datetime object.
        
        Args:
            date_string: Date string (e.g., "25/12/2024" or "25.12.2024")
        
        Returns:
            datetime object if valid, None otherwise
        """
        # Normalize separators
        normalized = date_string.replace('.', '/')
        
        # Try different formats
        formats = [
            "%d/%m/%Y",
            "%d/%m/%y",
            "%Y/%m/%d",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(normalized, fmt)
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_string}")
        return None
    
    def process_image(self, image_path: Path) -> OCRResult:
        """
        Process image to extract and validate expiry date.
        
        Args:
            image_path: Path to image file
        
        Returns:
            OCRResult with processing results
        """
        if not TESSERACT_AVAILABLE:
            return OCRResult(
                success=False,
                error="pytesseract not installed"
            )
        
        try:
            # Extract text
            text = self.extract_text(image_path)
            
            # Find date
            date_string = self.find_date_in_text(text)
            if not date_string:
                return OCRResult(
                    success=False,
                    raw_text=text,
                    error="No date pattern found in text"
                )
            
            # Parse date
            date_obj = self.parse_date(date_string)
            if not date_obj:
                return OCRResult(
                    success=False,
                    date_string=date_string,
                    raw_text=text,
                    error="Invalid date format"
                )
            
            # Check if already processed
            if self._last_processed_date and self._last_processed_date == date_obj:
                return OCRResult(
                    success=False,
                    date_string=date_string,
                    date_object=date_obj,
                    raw_text=text,
                    error="Date already processed"
                )
            
            # Check expiry
            today = datetime.now()
            is_expired = date_obj < today
            
            # Update last processed
            self._last_processed_date = date_obj
            
            return OCRResult(
                success=True,
                date_string=date_string,
                date_object=date_obj,
                is_expired=is_expired,
                raw_text=text
            )
            
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            return OCRResult(
                success=False,
                error=str(e)
            )
    
    def process_frame(self, frame) -> OCRResult:
        """
        Process a camera frame directly.
        
        Args:
            frame: OpenCV image frame
        
        Returns:
            OCRResult with processing results
        """
        # Preprocess
        processed = self.preprocess_image(frame)
        
        # Save temporary image
        temp_path = get_config().image_save_path
        cv2.imwrite(str(temp_path), processed)
        
        # Process
        return self.process_image(temp_path)
    
    def process_manual_date(self, date_string: str) -> OCRResult:
        """
        Process manually entered date string.
        
        Args:
            date_string: User input date string
        
        Returns:
            OCRResult with processing results
        """
        # Find date pattern in input
        found_date = self.find_date_in_text(date_string)
        if not found_date:
            return OCRResult(
                success=False,
                error="No valid date pattern in input"
            )
        
        # Parse date
        date_obj = self.parse_date(found_date)
        if not date_obj:
            return OCRResult(
                success=False,
                date_string=found_date,
                error="Invalid date format"
            )
        
        # Check if already processed
        if self._last_processed_date and self._last_processed_date == date_obj:
            return OCRResult(
                success=False,
                date_string=found_date,
                date_object=date_obj,
                error="Date already processed"
            )
        
        # Check expiry
        today = datetime.now()
        is_expired = date_obj < today
        
        # Update last processed
        self._last_processed_date = date_obj
        
        return OCRResult(
            success=True,
            date_string=found_date,
            date_object=date_obj,
            is_expired=is_expired
        )
    
    def reset_last_processed(self) -> None:
        """Reset the last processed date tracker."""
        self._last_processed_date = None
        logger.info("Last processed date reset")
    
    @property
    def is_available(self) -> bool:
        """Check if OCR is available."""
        return TESSERACT_AVAILABLE


def create_ocr_processor() -> OCRProcessor:
    """Factory function to create OCR processor."""
    return OCRProcessor()