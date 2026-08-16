"""Data formatters for PDF generation."""

import logging
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class DataFormatter:
    """Formatter for data before PDF generation."""

    @staticmethod
    def format_competencies(competencies: List[Dict]) -> List[Dict]:
        """Format competencies data.

        Args:
            competencies: Raw competencies list

        Returns:
            Formatted competencies
        """
        formatted = []
        for comp in competencies:
            formatted.append(
                {
                    "category": str(comp.get("category", "")).strip(),
                    "name": str(comp.get("name", "")).strip(),
                    "level": str(comp.get("level", "")).strip(),
                }
            )
        return formatted

    @staticmethod
    def format_experience(experience: List[Dict]) -> List[Dict]:
        """Format experience data.

        Args:
            experience: Raw experience list

        Returns:
            Formatted experience
        """
        formatted = []
        for exp in experience:
            formatted.append(
                {
                    "position": str(exp.get("position", "")).strip(),
                    "company": str(exp.get("company", "")).strip(),
                    "start_date": DataFormatter._format_date(exp.get("start_date", "")),
                    "end_date": DataFormatter._format_date(
                        exp.get("end_date", ""), allow_present=True
                    ),
                    "description": str(exp.get("description", "")).strip(),
                }
            )
        return formatted

    @staticmethod
    def format_education(education: List[Dict]) -> List[Dict]:
        """Format education data.

        Args:
            education: Raw education list

        Returns:
            Formatted education
        """
        formatted = []
        for edu in education:
            formatted.append(
                {
                    "degree": str(edu.get("degree", "")).strip(),
                    "school": str(edu.get("school", "")).strip(),
                    "field": str(edu.get("field", "")).strip(),
                    "year": str(edu.get("year", "")).strip(),
                }
            )
        return formatted

    @staticmethod
    def format_projects(projects: List[Dict]) -> List[Dict]:
        """Format projects data.

        Args:
            projects: Raw projects list

        Returns:
            Formatted projects
        """
        formatted = []
        for proj in projects:
            formatted.append(
                {
                    "name": str(proj.get("name", "")).strip(),
                    "description": str(proj.get("description", "")).strip(),
                    "technologies": [
                        str(t).strip() for t in proj.get("technologies", [])
                    ],
                    "link": proj.get("link"),
                }
            )
        return formatted

    @staticmethod
    def _format_date(date_str: str, allow_present: bool = False) -> str:
        """Format date string.

        Args:
            date_str: Date string in YYYY-MM format
            allow_present: Allow "present" as valid value

        Returns:
            Formatted date
        """
        if not date_str:
            return ""

        date_str = str(date_str).strip().lower()

        if allow_present and date_str == "present":
            return "present"

        # Try to parse YYYY-MM format
        try:
            # If already in YYYY-MM format, return as is
            if len(date_str) == 7 and date_str[4] == "-":
                return date_str
        except Exception:
            pass

        return date_str or ""

    @staticmethod
    def format_contact_info(email: str, phone: str, location: str) -> str:
        """Format contact information string.

        Args:
            email: Email address
            phone: Phone number
            location: Location

        Returns:
            Formatted contact string
        """
        parts = []
        if email:
            parts.append(str(email).strip())
        if phone:
            parts.append(str(phone).strip())
        if location:
            parts.append(str(location).strip())

        return " | ".join(parts)
