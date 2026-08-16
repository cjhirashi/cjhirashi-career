"""PDF Service for low-level PDF operations."""

import logging
from io import BytesIO
from datetime import datetime

logger = logging.getLogger(__name__)


class PDFService:
    """Service for PDF operations."""

    @staticmethod
    def get_pdf_size(pdf_buffer: BytesIO) -> int:
        """Get PDF buffer size in bytes.

        Args:
            pdf_buffer: BytesIO object containing PDF data

        Returns:
            Size in bytes
        """
        current_pos = pdf_buffer.tell()
        pdf_buffer.seek(0, 2)  # Seek to end
        size = pdf_buffer.tell()
        pdf_buffer.seek(current_pos)  # Return to original position
        return size

    @staticmethod
    def generate_filename(
        base_name: str,
        name: str,
        suffix: str = "",
    ) -> str:
        """Generate PDF filename.

        Args:
            base_name: Base name (e.g., 'CV', 'CoverLetter')
            name: Person name
            suffix: Optional suffix

        Returns:
            Formatted filename
        """
        # Sanitize name: remove special characters, replace spaces
        clean_name = "".join(c if c.isalnum() or c in (" ", "-") else "" for c in name)
        clean_name = clean_name.replace(" ", "").strip()

        if suffix:
            return f"{base_name}_{clean_name}_{suffix}.pdf"
        return f"{base_name}_{clean_name}.pdf"

    @staticmethod
    def get_current_timestamp() -> str:
        """Get current timestamp in ISO format.

        Returns:
            ISO format timestamp
        """
        return datetime.utcnow().isoformat()
