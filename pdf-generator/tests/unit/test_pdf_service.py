"""Unit tests for PDF Service."""

import pytest
from io import BytesIO
from src.services.pdf_service import PDFService


class TestPDFService:
    """Test PDF Service."""

    def test_get_pdf_size_with_valid_buffer(self):
        """Test getting PDF size from valid buffer."""
        pdf_service = PDFService()
        buffer = BytesIO(b"PDF content here")
        size = pdf_service.get_pdf_size(buffer)
        assert isinstance(size, int)
        assert size == len(b"PDF content here")

    def test_get_pdf_size_empty_buffer(self):
        """Test getting PDF size from empty buffer."""
        pdf_service = PDFService()
        buffer = BytesIO()
        size = pdf_service.get_pdf_size(buffer)
        assert isinstance(size, int)
        assert size == 0

    def test_get_pdf_size_large_buffer(self):
        """Test getting PDF size from large buffer."""
        pdf_service = PDFService()
        content = b"x" * 1000000  # 1MB
        buffer = BytesIO(content)
        size = pdf_service.get_pdf_size(buffer)
        assert isinstance(size, int)
        assert size == 1000000

    def test_get_pdf_size_buffer_at_non_zero_position(self):
        """Test getting PDF size from buffer at non-zero position."""
        pdf_service = PDFService()
        buffer = BytesIO(b"PDF content here")
        buffer.seek(5)  # Move position
        size = pdf_service.get_pdf_size(buffer)
        # Should return total buffer size, not size from current position
        assert size == len(b"PDF content here")

    def test_get_pdf_size_preserves_buffer_position(self):
        """Test that getting PDF size doesn't change buffer position."""
        pdf_service = PDFService()
        buffer = BytesIO(b"PDF content here")
        buffer.seek(0)
        initial_pos = buffer.tell()
        pdf_service.get_pdf_size(buffer)
        # Buffer position should be at start for streaming
        assert buffer.tell() == 0
