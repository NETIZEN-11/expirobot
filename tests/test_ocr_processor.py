"""Tests for ExpirioBot OCR processor module."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from expiriobot.ocr_processor import OCRProcessor, OCRResult, create_ocr_processor
from expiriobot.config import OCRConfig


class TestOCRProcessor:
    """Test cases for OCRProcessor."""
    
    @pytest.fixture
    def ocr_config(self):
        """Create test OCR config."""
        return OCRConfig(
            tesseract_cmd="",
            date_patterns=[r'\b\d{2}[./]\d{2}[./]\d{4}\b'],
            threshold_value=128
        )
    
    @pytest.fixture
    def processor(self, ocr_config):
        """Create OCR processor instance."""
        return OCRProcessor(config=ocr_config)
    
    def test_parse_date_valid_formats(self, processor):
        """Test date parsing with valid formats."""
        test_cases = [
            ("25/12/2024", datetime(2024, 12, 25)),
            ("25.12.2024", datetime(2024, 12, 25)),
            ("01/01/2023", datetime(2023, 1, 1)),
            ("31/12/2025", datetime(2025, 12, 31)),
        ]
        
        for date_str, expected in test_cases:
            result = processor.parse_date(date_str)
            assert result == expected, f"Failed for {date_str}"
    
    def test_parse_date_invalid(self, processor):
        """Test date parsing with invalid formats."""
        invalid_dates = [
            "not a date",
            "25/13/2024",  # Invalid month
            "32/01/2024",  # Invalid day
        ]
        
        for date_str in invalid_dates:
            result = processor.parse_date(date_str)
            assert result is None, f"Should have failed for {date_str}"
        
        # YYYY/MM/DD is actually supported by the parser
        result = processor.parse_date("2024/12/25")
        assert result is not None
        assert result == datetime(2024, 12, 25)
    
    def test_find_date_in_text(self, processor):
        """Test finding date pattern in text."""
        text_with_date = "Product expires on 25/12/2024 please check"
        result = processor.find_date_in_text(text_with_date)
        assert result == "25/12/2024"
        
        text_without_date = "No date here"
        result = processor.find_date_in_text(text_without_date)
        assert result is None
    
    def test_process_manual_date_valid(self, processor):
        """Test processing manual date input."""
        result = processor.process_manual_date("25/12/2024")
        
        assert result.success is True
        assert result.date_string == "25/12/2024"
        assert result.date_object == datetime(2024, 12, 25)
        assert result.is_expired is not None
    
    def test_process_manual_date_invalid(self, processor):
        """Test processing invalid manual date input."""
        result = processor.process_manual_date("not a date")
        
        assert result.success is False
        assert result.error is not None
    
    def test_process_manual_date_already_processed(self, processor):
        """Test processing same date twice."""
        # First time
        result1 = processor.process_manual_date("25/12/2024")
        assert result1.success is True
        
        # Second time (should fail as already processed)
        result2 = processor.process_manual_date("25/12/2024")
        assert result2.success is False
        assert "already processed" in result2.error.lower()
    
    def test_reset_last_processed(self, processor):
        """Test resetting last processed date."""
        # Process a date
        processor.process_manual_date("25/12/2024")
        
        # Reset
        processor.reset_last_processed()
        
        # Should be able to process again
        result = processor.process_manual_date("25/12/2024")
        assert result.success is True
    
    @patch('expiriobot.ocr_processor.cv2')
    @patch('expiriobot.ocr_processor.Image')
    @patch('expiriobot.ocr_processor.pytesseract')
    def test_process_image_success(self, mock_tesseract, mock_image, mock_cv2, processor):
        """Test successful image processing."""
        # Mock image processing
        mock_img = Mock()
        mock_image.open.return_value = mock_img
        mock_tesseract.image_to_string.return_value = "Expiry: 25/12/2024"
        
        # Mock cv2.imread
        mock_cv2.imread.return_value = Mock()
        
        with patch('expiriobot.ocr_processor.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.image_save_path = Path("test.jpg")
            mock_get_config.return_value = mock_config
            
            result = processor.process_image(Path("test.jpg"))
        
        assert result.success is True
        assert result.date_string == "25/12/2024"
    
    def test_is_available_without_tesseract(self):
        """Test availability check without tesseract."""
        with patch('expiriobot.ocr_processor.TESSERACT_AVAILABLE', False):
            processor = create_ocr_processor()
            assert processor.is_available is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])