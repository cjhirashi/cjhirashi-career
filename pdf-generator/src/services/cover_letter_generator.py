"""Cover Letter Generator Service."""

import logging
from io import BytesIO

from src.templates.cover_letter_template import CoverLetterTemplate
from src.services.pdf_service import PDFService

logger = logging.getLogger(__name__)


class CoverLetterGenerator:
    """Service for generating Cover Letter PDFs."""

    def __init__(self):
        """Initialize Cover Letter Generator."""
        self.pdf_service = PDFService()

    def generate_cover_letter(
        self,
        name: str,
        email: str,
        date: str,
        company_name: str,
        company_address: str,
        recipient_name: str,
        position: str,
        body: str,
        closing_statement: str,
        signature: str,
    ) -> BytesIO:
        """Generate Cover Letter PDF.

        Args:
            name: Sender name
            email: Sender email
            date: Letter date (YYYY-MM-DD format)
            company_name: Target company name
            company_address: Company address
            recipient_name: Recipient name
            position: Position applied for
            body: Letter body content
            closing_statement: Closing statement before signature
            signature: Sender signature

        Returns:
            BytesIO object with PDF data

        Raises:
            ValueError: If generation fails
        """
        try:
            logger.info(f"Generating Cover Letter for {name} at {company_name}")

            # Create template
            template = CoverLetterTemplate(
                name=name,
                email=email,
            )

            # Generate PDF
            pdf_buffer = template.generate(
                date=date,
                company_name=company_name,
                company_address=company_address,
                recipient_name=recipient_name,
                position=position,
                body=body,
                closing_statement=closing_statement,
                signature=signature,
            )

            logger.info(f"Cover Letter generated successfully for {name}")
            return pdf_buffer

        except Exception as e:
            logger.error(f"Error generating Cover Letter: {str(e)}")
            raise ValueError(f"Failed to generate Cover Letter: {str(e)}")

    def get_cover_letter_filename(self, name: str, company: str) -> str:
        """Get formatted Cover Letter filename.

        Args:
            name: Person name
            company: Company name

        Returns:
            Formatted filename
        """
        return self.pdf_service.generate_filename(
            "CoverLetter", name, suffix=company.replace(" ", "")[:10]
        )
