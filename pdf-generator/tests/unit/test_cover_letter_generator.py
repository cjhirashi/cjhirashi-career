"""Unit tests for Cover Letter Generator."""

import pytest
from io import BytesIO

from src.services.cover_letter_generator import CoverLetterGenerator
from tests.fixtures.sample_data import (
    get_sample_cover_letter_data,
    get_minimal_cover_letter_data,
)


@pytest.fixture
def cover_letter_generator():
    """Get Cover Letter generator instance."""
    return CoverLetterGenerator()


@pytest.fixture
def sample_cover_letter_data():
    """Get sample Cover Letter data."""
    return get_sample_cover_letter_data()


@pytest.fixture
def minimal_cover_letter_data():
    """Get minimal Cover Letter data."""
    return get_minimal_cover_letter_data()


class TestCoverLetterGenerator:
    """Test Cover Letter Generator."""

    def test_generate_cover_letter_with_complete_data(
        self, cover_letter_generator, sample_cover_letter_data
    ):
        """Test Cover Letter generation with complete data."""
        pdf_buffer = cover_letter_generator.generate_cover_letter(
            name=sample_cover_letter_data["name"],
            email=sample_cover_letter_data["email"],
            date=sample_cover_letter_data["date"],
            company_name=sample_cover_letter_data["company_name"],
            company_address=sample_cover_letter_data["company_address"],
            recipient_name=sample_cover_letter_data["recipient_name"],
            position=sample_cover_letter_data["position"],
            body=sample_cover_letter_data["body"],
            closing_statement=sample_cover_letter_data["closing_statement"],
            signature=sample_cover_letter_data["signature"],
        )

        # Assert PDF buffer is valid
        assert isinstance(pdf_buffer, BytesIO)
        assert pdf_buffer.tell() == 0  # Should be at start
        assert pdf_buffer.getbuffer().nbytes > 0  # Should have content

    def test_generate_cover_letter_with_minimal_data(
        self, cover_letter_generator, minimal_cover_letter_data
    ):
        """Test Cover Letter generation with minimal data."""
        pdf_buffer = cover_letter_generator.generate_cover_letter(
            name=minimal_cover_letter_data["name"],
            email=minimal_cover_letter_data["email"],
            date=minimal_cover_letter_data["date"],
            company_name=minimal_cover_letter_data["company_name"],
            company_address=minimal_cover_letter_data["company_address"],
            recipient_name=minimal_cover_letter_data["recipient_name"],
            position=minimal_cover_letter_data["position"],
            body=minimal_cover_letter_data["body"],
            closing_statement=minimal_cover_letter_data["closing_statement"],
            signature=minimal_cover_letter_data["signature"],
        )

        # Assert PDF buffer is valid
        assert isinstance(pdf_buffer, BytesIO)
        assert pdf_buffer.getbuffer().nbytes > 0

    def test_get_cover_letter_filename(self, cover_letter_generator):
        """Test Cover Letter filename generation."""
        filename = cover_letter_generator.get_cover_letter_filename(
            "Carlos Jiménez Hirashi", "Tech Company Inc"
        )
        assert filename.startswith("CoverLetter_")
        assert filename.endswith(".pdf")
        assert "Carlos" in filename

    def test_get_cover_letter_filename_with_special_company_name(
        self, cover_letter_generator
    ):
        """Test Cover Letter filename with special company characters."""
        filename = cover_letter_generator.get_cover_letter_filename(
            "John Doe", "O'Brien & Sons Inc."
        )
        assert filename.endswith(".pdf")
        assert "CoverLetter_" in filename

    def test_generate_cover_letter_with_multiline_body(
        self, cover_letter_generator
    ):
        """Test Cover Letter with multiline body content."""
        multiline_body = """First paragraph of the cover letter body.

Second paragraph with more details about the position and interest.

Third paragraph highlighting relevant experience."""

        pdf_buffer = cover_letter_generator.generate_cover_letter(
            name="Test User",
            email="test@example.com",
            date="2024-08-16",
            company_name="Test Company",
            company_address="123 Main St, City, State",
            recipient_name="Hiring Manager",
            position="Test Position",
            body=multiline_body,
            closing_statement="Thank you for your consideration",
            signature="Test User",
        )

        assert isinstance(pdf_buffer, BytesIO)
        assert pdf_buffer.getbuffer().nbytes > 0

    def test_generate_cover_letter_with_date_formats(self, cover_letter_generator):
        """Test Cover Letter generation with different valid dates."""
        # Test various date formats that should pass validation
        dates = [
            "2024-01-01",
            "2024-12-31",
            "2000-06-15",
        ]

        for date in dates:
            pdf_buffer = cover_letter_generator.generate_cover_letter(
                name="Test User",
                email="test@example.com",
                date=date,
                company_name="Test Company",
                company_address="123 Main St, City",
                recipient_name="Hiring Manager",
                position="Position",
                body="This is a comprehensive cover letter body with sufficient content.",
                closing_statement="Thank you for the opportunity",
                signature="Test User",
            )

            assert isinstance(pdf_buffer, BytesIO)
            assert pdf_buffer.getbuffer().nbytes > 0

    def test_generate_cover_letter_long_content(self, cover_letter_generator):
        """Test Cover Letter with longer content."""
        long_body = """I am writing to express my strong interest in this position.

With years of professional experience and a demonstrated commitment to excellence, I believe I am well-suited for this role. My background includes substantial expertise in relevant areas, and I have consistently delivered results in similar capacities.

Throughout my career, I have developed strong technical skills combined with excellent communication abilities. I am particularly drawn to this opportunity because it aligns with my career goals and professional values.

I am eager to contribute my skills and experience to your organization and would welcome the opportunity to discuss how I can add value to your team."""

        pdf_buffer = cover_letter_generator.generate_cover_letter(
            name="Complex Name User",
            email="complex@example.com",
            date="2024-08-16",
            company_name="Very Important Company",
            company_address="123 Business Avenue, Suite 500, Major City, State 12345",
            recipient_name="Director of Hiring",
            position="Senior Staff Engineer",
            body=long_body,
            closing_statement="I look forward to discussing this exciting opportunity at your earliest convenience.",
            signature="Complex Name User",
        )

        assert isinstance(pdf_buffer, BytesIO)
        assert pdf_buffer.getbuffer().nbytes > 0
