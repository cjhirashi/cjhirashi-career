"""Integration tests for Cover Letter generation endpoint."""

import pytest
from fastapi.testclient import TestClient

from src.main import app
from tests.fixtures.sample_data import (
    get_sample_cover_letter_data,
    get_minimal_cover_letter_data,
)


@pytest.fixture
def client():
    """Get FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_cover_letter_data():
    """Get sample Cover Letter data."""
    return get_sample_cover_letter_data()


@pytest.fixture
def minimal_cover_letter_data():
    """Get minimal Cover Letter data."""
    return get_minimal_cover_letter_data()


class TestGenerateCoverLetterEndpoint:
    """Test Cover Letter generation endpoint."""

    def test_generate_cover_letter_success(self, client, sample_cover_letter_data):
        """Test successful Cover Letter generation."""
        response = client.post("/generate/cover-letter", json=sample_cover_letter_data)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert ".pdf" in response.headers["content-disposition"]
        assert len(response.content) > 0

    def test_generate_cover_letter_minimal_data(
        self, client, minimal_cover_letter_data
    ):
        """Test Cover Letter generation with minimal data."""
        response = client.post("/generate/cover-letter", json=minimal_cover_letter_data)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 0

    def test_generate_cover_letter_filename_format(self, client, sample_cover_letter_data):
        """Test that filename is properly formatted."""
        response = client.post("/generate/cover-letter", json=sample_cover_letter_data)

        assert response.status_code == 200
        disposition = response.headers["content-disposition"]
        assert "CoverLetter_" in disposition
        assert ".pdf" in disposition

    def test_generate_cover_letter_missing_name(self, client, sample_cover_letter_data):
        """Test Cover Letter generation with missing name."""
        sample_cover_letter_data["name"] = ""
        response = client.post("/generate/cover-letter", json=sample_cover_letter_data)

        assert response.status_code == 400

    def test_generate_cover_letter_invalid_email(self, client, sample_cover_letter_data):
        """Test Cover Letter generation with invalid email."""
        sample_cover_letter_data["email"] = "not-an-email"
        response = client.post("/generate/cover-letter", json=sample_cover_letter_data)

        assert response.status_code == 422

    def test_generate_cover_letter_invalid_date_format(
        self, client, sample_cover_letter_data
    ):
        """Test Cover Letter generation with invalid date format."""
        sample_cover_letter_data["date"] = "08/16/2024"  # Wrong format
        response = client.post("/generate/cover-letter", json=sample_cover_letter_data)

        assert response.status_code == 422

    def test_generate_cover_letter_missing_required_fields(self, client):
        """Test Cover Letter generation with missing required fields."""
        incomplete_data = {
            "name": "Test User",
            "email": "test@example.com",
            # Missing other required fields
        }
        response = client.post("/generate/cover-letter", json=incomplete_data)

        assert response.status_code == 422

    def test_generate_cover_letter_short_body(self, client, sample_cover_letter_data):
        """Test Cover Letter with body that's too short."""
        sample_cover_letter_data["body"] = "Too short"
        response = client.post("/generate/cover-letter", json=sample_cover_letter_data)

        assert response.status_code == 400

    def test_generate_cover_letter_short_closing_statement(
        self, client, sample_cover_letter_data
    ):
        """Test Cover Letter with closing statement that's too short."""
        sample_cover_letter_data["closing_statement"] = "Short"
        response = client.post("/generate/cover-letter", json=sample_cover_letter_data)

        assert response.status_code == 400

    def test_generate_cover_letter_multiple_requests(
        self, client, sample_cover_letter_data, minimal_cover_letter_data
    ):
        """Test generating Cover Letters for different scenarios."""
        response1 = client.post("/generate/cover-letter", json=sample_cover_letter_data)
        response2 = client.post("/generate/cover-letter", json=minimal_cover_letter_data)

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert len(response1.content) > 0
        assert len(response2.content) > 0

    def test_generate_cover_letter_long_text_fields(self, client, minimal_cover_letter_data):
        """Test Cover Letter with very long text fields."""
        minimal_cover_letter_data["body"] = "A" * 2000
        minimal_cover_letter_data["closing_statement"] = "B" * 500

        response = client.post("/generate/cover-letter", json=minimal_cover_letter_data)

        assert response.status_code == 200
        assert len(response.content) > 0

    def test_generate_cover_letter_special_characters_in_name(
        self, client, minimal_cover_letter_data
    ):
        """Test Cover Letter with special characters in name."""
        minimal_cover_letter_data["name"] = "José María O'Brien-Smith"

        response = client.post("/generate/cover-letter", json=minimal_cover_letter_data)

        assert response.status_code == 200
        assert len(response.content) > 0

    def test_generate_cover_letter_special_characters_in_company(
        self, client, minimal_cover_letter_data
    ):
        """Test Cover Letter with special characters in company name."""
        minimal_cover_letter_data["company_name"] = "O'Brien & Sons Inc."

        response = client.post("/generate/cover-letter", json=minimal_cover_letter_data)

        assert response.status_code == 200
        assert len(response.content) > 0

    def test_generate_cover_letter_response_headers(self, client, sample_cover_letter_data):
        """Test response headers are correct."""
        response = client.post("/generate/cover-letter", json=sample_cover_letter_data)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "content-disposition" in response.headers
        assert "attachment" in response.headers["content-disposition"]

    def test_generate_cover_letter_malformed_json(self, client):
        """Test with malformed JSON."""
        response = client.post(
            "/generate/cover-letter",
            content="not valid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422

    def test_generate_cover_letter_multiline_body(self, client, minimal_cover_letter_data):
        """Test Cover Letter with multiline body."""
        minimal_cover_letter_data["body"] = """First paragraph.

Second paragraph with more details.

Third paragraph."""

        response = client.post("/generate/cover-letter", json=minimal_cover_letter_data)

        assert response.status_code == 200
        assert len(response.content) > 0

    def test_generate_cover_letter_valid_dates(self, client, minimal_cover_letter_data):
        """Test Cover Letter with various valid dates."""
        dates = ["2024-01-01", "2024-12-31", "2000-06-15"]

        for date in dates:
            minimal_cover_letter_data["date"] = date
            response = client.post(
                "/generate/cover-letter", json=minimal_cover_letter_data
            )

            assert response.status_code == 200
            assert len(response.content) > 0

    def test_generate_cover_letter_different_companies(self, client, minimal_cover_letter_data):
        """Test generating cover letters for different companies."""
        companies = [
            "Tech Company Inc.",
            "Global Solutions Ltd.",
            "Innovation Labs",
        ]

        for company in companies:
            minimal_cover_letter_data["company_name"] = company
            response = client.post(
                "/generate/cover-letter", json=minimal_cover_letter_data
            )

            assert response.status_code == 200
            assert company.replace(" ", "")[:10] in response.headers[
                "content-disposition"
            ]

    def test_generate_cover_letter_empty_string_fields(
        self, client, minimal_cover_letter_data
    ):
        """Test Cover Letter with empty string fields."""
        minimal_cover_letter_data["recipient_name"] = ""
        response = client.post("/generate/cover-letter", json=minimal_cover_letter_data)

        assert response.status_code == 400

    def test_generate_cover_letter_whitespace_only_fields(
        self, client, minimal_cover_letter_data
    ):
        """Test Cover Letter with whitespace-only fields."""
        minimal_cover_letter_data["signature"] = "   "
        response = client.post("/generate/cover-letter", json=minimal_cover_letter_data)

        assert response.status_code == 400
