"""Input validators for PDF Generator."""

import logging
import re
from typing import List, Dict

logger = logging.getLogger(__name__)


class InputValidator:
    """Validator for input data."""

    @staticmethod
    def validate_cv_data(
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
    ) -> None:
        """Validate CV data.

        Args:
            name: Full name
            email: Email address
            phone: Phone number
            location: Location
            ikigai: IKIGAI text
            about: About text
            competencies: Competencies list
            experience: Experience list
            education: Education list
            projects: Projects list

        Raises:
            ValueError: If validation fails
        """
        # Basic field validation
        if not name or not name.strip():
            raise ValueError("Name is required")

        if not email or "@" not in email:
            raise ValueError("Valid email is required")

        if not phone or len(phone.replace(" ", "").replace("-", "")) < 5:
            raise ValueError("Valid phone number is required")

        if not location or not location.strip():
            raise ValueError("Location is required")

        if not ikigai or len(ikigai) < 10:
            raise ValueError("IKIGAI must be at least 10 characters")

        if not about or len(about) < 20:
            raise ValueError("About section must be at least 20 characters")

        # Validate competencies
        if not competencies:
            raise ValueError("At least one competency is required")

        for comp in competencies:
            if not comp.get("name"):
                raise ValueError("Competency name is required")
            if not comp.get("level"):
                raise ValueError("Competency level is required")
            if not comp.get("category"):
                raise ValueError("Competency category is required")

        # Validate experience if present
        for exp in experience:
            if not exp.get("position"):
                raise ValueError("Experience position is required")
            if not exp.get("company"):
                raise ValueError("Experience company is required")
            if not exp.get("description"):
                raise ValueError("Experience description is required")

        # Validate education if present
        for edu in education:
            if not edu.get("degree"):
                raise ValueError("Education degree is required")
            if not edu.get("school"):
                raise ValueError("Education school is required")
            if not edu.get("field"):
                raise ValueError("Education field is required")
            if not edu.get("year"):
                raise ValueError("Education year is required")

        # Validate projects if present
        for proj in projects:
            if not proj.get("name"):
                raise ValueError("Project name is required")
            if not proj.get("description"):
                raise ValueError("Project description is required")
            if not proj.get("technologies"):
                raise ValueError("Project technologies are required")

        logger.info("CV data validation passed")

    @staticmethod
    def validate_cover_letter_data(
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
    ) -> None:
        """Validate Cover Letter data.

        Args:
            name: Sender name
            email: Sender email
            date: Letter date
            company_name: Company name
            company_address: Company address
            recipient_name: Recipient name
            position: Position
            body: Letter body
            closing_statement: Closing statement
            signature: Signature

        Raises:
            ValueError: If validation fails
        """
        # Basic field validation
        if not name or not name.strip():
            raise ValueError("Name is required")

        if not email or "@" not in email:
            raise ValueError("Valid email is required")

        if not date or not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
            raise ValueError("Valid date (YYYY-MM-DD) is required")

        if not company_name or not company_name.strip():
            raise ValueError("Company name is required")

        if not company_address or not company_address.strip():
            raise ValueError("Company address is required")

        if not recipient_name or not recipient_name.strip():
            raise ValueError("Recipient name is required")

        if not position or not position.strip():
            raise ValueError("Position is required")

        if not body or len(body) < 50:
            raise ValueError("Letter body must be at least 50 characters")

        if not closing_statement or len(closing_statement) < 10:
            raise ValueError("Closing statement must be at least 10 characters")

        if not signature or not signature.strip():
            raise ValueError("Signature is required")

        logger.info("Cover Letter data validation passed")

    @staticmethod
    def sanitize_text(text: str) -> str:
        """Sanitize text for PDF output.

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text
        """
        if not text:
            return ""

        # Remove potential PDF injection characters
        text = text.replace("<<", "")
        text = text.replace(">>", "")

        return text.strip()
