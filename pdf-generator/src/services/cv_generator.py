"""CV Generator Service."""

import logging
from io import BytesIO
from typing import List, Dict

from src.templates.cv_template import CVTemplate
from src.services.pdf_service import PDFService

logger = logging.getLogger(__name__)


class CVGenerator:
    """Service for generating CV PDFs."""

    def __init__(self):
        """Initialize CV Generator."""
        self.pdf_service = PDFService()

    def generate_cv(
        self,
        name: str,
        email: str,
        phone: str,
        location: str,
        ikigai: str,
        about: str,
        competencies: List[Dict],
        experience: List[Dict],
        education: List[Dict],
        projects: List[Dict],
    ) -> BytesIO:
        """Generate CV PDF.

        Args:
            name: Full name
            email: Email address
            phone: Phone number
            location: Location
            ikigai: IKIGAI/Professional summary
            about: About/Professional bio
            competencies: List of competency dictionaries
            experience: List of experience dictionaries
            education: List of education dictionaries
            projects: List of project dictionaries

        Returns:
            BytesIO object with PDF data

        Raises:
            ValueError: If CV generation fails
        """
        try:
            logger.info(f"Generating CV for {name}")

            # Create template
            template = CVTemplate(
                name=name,
                email=email,
                phone=phone,
                location=location,
                ikigai=ikigai,
                about=about,
            )

            # Generate PDF
            pdf_buffer = template.generate(
                competencies=competencies,
                experience=experience,
                education=education,
                projects=projects,
            )

            logger.info(f"CV generated successfully for {name}")
            return pdf_buffer

        except Exception as e:
            logger.error(f"Error generating CV: {str(e)}")
            raise ValueError(f"Failed to generate CV: {str(e)}")

    def get_cv_filename(self, name: str) -> str:
        """Get formatted CV filename.

        Args:
            name: Person name

        Returns:
            Formatted filename
        """
        return self.pdf_service.generate_filename("CV", name)
