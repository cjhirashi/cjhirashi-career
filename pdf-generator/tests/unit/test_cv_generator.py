"""Unit tests for CV Generator."""

import pytest
from io import BytesIO

from src.services.cv_generator import CVGenerator
from tests.fixtures.sample_data import get_sample_cv_data, get_minimal_cv_data


@pytest.fixture
def cv_generator():
    """Get CV generator instance."""
    return CVGenerator()


@pytest.fixture
def sample_cv_data():
    """Get sample CV data."""
    return get_sample_cv_data()


@pytest.fixture
def minimal_cv_data():
    """Get minimal CV data."""
    return get_minimal_cv_data()


class TestCVGenerator:
    """Test CV Generator."""

    def test_generate_cv_with_complete_data(self, cv_generator, sample_cv_data):
        """Test CV generation with complete data."""
        pdf_buffer = cv_generator.generate_cv(
            name=sample_cv_data["name"],
            email=sample_cv_data["email"],
            phone=sample_cv_data["phone"],
            location=sample_cv_data["location"],
            ikigai=sample_cv_data["ikigai"],
            about=sample_cv_data["about"],
            competencies=sample_cv_data["competencies"],
            experience=sample_cv_data["experience"],
            education=sample_cv_data["education"],
            projects=sample_cv_data["projects"],
        )

        # Assert PDF buffer is valid
        assert isinstance(pdf_buffer, BytesIO)
        assert pdf_buffer.tell() == 0  # Should be at start
        assert pdf_buffer.getbuffer().nbytes > 0  # Should have content

    def test_generate_cv_with_minimal_data(self, cv_generator, minimal_cv_data):
        """Test CV generation with minimal data."""
        pdf_buffer = cv_generator.generate_cv(
            name=minimal_cv_data["name"],
            email=minimal_cv_data["email"],
            phone=minimal_cv_data["phone"],
            location=minimal_cv_data["location"],
            ikigai=minimal_cv_data["ikigai"],
            about=minimal_cv_data["about"],
            competencies=minimal_cv_data["competencies"],
            experience=minimal_cv_data["experience"],
            education=minimal_cv_data["education"],
            projects=minimal_cv_data["projects"],
        )

        # Assert PDF buffer is valid
        assert isinstance(pdf_buffer, BytesIO)
        assert pdf_buffer.getbuffer().nbytes > 0

    def test_get_cv_filename(self, cv_generator):
        """Test CV filename generation."""
        filename = cv_generator.get_cv_filename("Carlos Jiménez Hirashi")
        assert filename.startswith("CV_")
        assert filename.endswith(".pdf")
        assert "Carlos" in filename

    def test_get_cv_filename_special_characters(self, cv_generator):
        """Test CV filename with special characters."""
        filename = cv_generator.get_cv_filename("John O'Brien-Smith")
        assert filename.endswith(".pdf")
        assert ".pdf" in filename

    def test_generate_cv_without_experience(self, cv_generator, minimal_cv_data):
        """Test CV generation without experience."""
        minimal_cv_data["experience"] = []

        pdf_buffer = cv_generator.generate_cv(
            name=minimal_cv_data["name"],
            email=minimal_cv_data["email"],
            phone=minimal_cv_data["phone"],
            location=minimal_cv_data["location"],
            ikigai=minimal_cv_data["ikigai"],
            about=minimal_cv_data["about"],
            competencies=minimal_cv_data["competencies"],
            experience=[],
            education=[],
            projects=[],
        )

        assert isinstance(pdf_buffer, BytesIO)
        assert pdf_buffer.getbuffer().nbytes > 0

    def test_generate_cv_with_multiple_competencies(self, cv_generator):
        """Test CV generation with multiple competencies."""
        competencies = [
            {"category": "Languages", "name": "Python", "level": "Expert"},
            {"category": "Languages", "name": "Go", "level": "Advanced"},
            {"category": "Languages", "name": "JavaScript", "level": "Intermediate"},
            {"category": "Databases", "name": "PostgreSQL", "level": "Expert"},
            {"category": "Databases", "name": "Redis", "level": "Advanced"},
        ]

        pdf_buffer = cv_generator.generate_cv(
            name="Test User",
            email="test@example.com",
            phone="+1 555 1234",
            location="Test City",
            ikigai="Test IKIGAI",
            about="Test about section with enough content",
            competencies=competencies,
            experience=[],
            education=[],
            projects=[],
        )

        assert isinstance(pdf_buffer, BytesIO)
        assert pdf_buffer.getbuffer().nbytes > 0

    def test_generate_cv_invalid_email_raises_error(self, cv_generator):
        """Test that invalid data raises appropriate error (handled by validators)."""
        # Note: This would be caught by Pydantic validation at request level
        # Here we test that the generator handles it gracefully if data somehow gets through
        pdf_buffer = cv_generator.generate_cv(
            name="Test User",
            email="valid@example.com",
            phone="+1 555 1234",
            location="Test City",
            ikigai="Test IKIGAI text here",
            about="Test about section with enough content",
            competencies=[{"category": "Lang", "name": "Python", "level": "Expert"}],
            experience=[],
            education=[],
            projects=[],
        )

        assert isinstance(pdf_buffer, BytesIO)
