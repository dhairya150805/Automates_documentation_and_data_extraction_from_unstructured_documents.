import pytest
import os
import tempfile
from unittest.mock import Mock, patch
from ai.ocr import perform_ocr

def test_ocr_text_file():
    """Test OCR on a text file"""
    test_content = "This is a test document for OCR processing"
    fd, temp_path = tempfile.mkstemp(suffix='.txt')
    try:
        with os.fdopen(fd, 'w') as tmp:
            tmp.write(test_content)
        
        result = perform_ocr(temp_path)
        assert "text" in result
        assert "boxes" in result
        assert result["text"] == test_content
        assert result["boxes"] == []  # Text files don't have bounding boxes
    finally:
        try:
            os.unlink(temp_path)
        except (OSError, PermissionError):
            pass  # Ignore cleanup errors on Windows

def test_ocr_unsupported_file():
    """Test OCR on unsupported file type"""
    fd, temp_path = tempfile.mkstemp(suffix='.xyz')
    try:
        os.close(fd)  # Close file descriptor immediately
        with pytest.raises(ValueError, match="Unsupported file type"):
            perform_ocr(temp_path)
    finally:
        try:
            os.unlink(temp_path)
        except (OSError, PermissionError):
            pass

@patch('cv2.imread')
def test_ocr_image_file(mock_imread):
    """Test OCR on image file"""
    # Mock cv2.imread to return None (simulating file not found)
    mock_imread.return_value = None
    
    with pytest.raises(ValueError, match="Unsupported file type"):
        perform_ocr("test.jpg")

def test_ocr_markdown_file():
    """Test OCR on markdown file"""
    test_content = "# Test Document\n\nThis is a markdown test."
    fd, temp_path = tempfile.mkstemp(suffix='.md')
    try:
        with os.fdopen(fd, 'w') as tmp:
            tmp.write(test_content)
        
        result = perform_ocr(temp_path)
        assert result["text"] == test_content
        assert result["boxes"] == []
    finally:
        try:
            os.unlink(temp_path)
        except (OSError, PermissionError):
            pass

@patch('backend.ai.ocr.transcribe_audio')
def test_ocr_audio_file_no_transcriber(mock_transcribe):
    """Test OCR on audio file when transcriber is not available"""
    # Create mock transcriber that returns None (not available)
    mock_transcribe.return_value = None
    
    with pytest.raises(ValueError, match="Audio transcription is not configured"):
        perform_ocr("test.wav")
