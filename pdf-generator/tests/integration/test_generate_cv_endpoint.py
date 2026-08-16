"""Integration tests for CV generation endpoint."""

import pytest
from fastapi.testclient import TestClient

from src.main import app
from tests.fixtures.sample_data import get_sample_cv_data, get_minimal_cv_data


@pytest.fixture
def client():
    """Get FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_cv_data():
    """Get sample CV data."""
    return get_sample_cv_data()


@pytest.fixture
def minimal_cv_data():
    """Get minimal CV data."""
    return get_minimal_cv_data()


class TestGenerateCVEndpoint:
    """Test CV generation endpoint."""

    def test_generate_cv_success(self, client, sample_cv_data):
        """Test successful CV generation."""
        response = client.post("/generate/cv", json=sample_cv_data)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert ".pdf" in response.headers["content-disposition"]
        assert len(response.content) > 0

    def test_generate_cv_minimal_data(self, client, minimal_cv_data):
        """Test CV generation with minimal data."""
        response = client.post("/generate/cv", json=minimal_cv_data)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 0

    def test_generate_cv_filename_format(self, client, sample_cv_data):
        """Test that filename is properly formatted."""
        response = client.post("/generate/cv", json=sample_cv_data)

        assert response.status_code == 200
        disposition = response.headers["content-disposition"]
        assert "CV_" in disposition
        assert ".pdf" in disposition

    def test_generate_cv_missing_name(self, client, sample_cv_data):
        """Test CV generation with missing name."""
        sample_cv_data["name"] = ""
        response = client.post("/generate/cv", json=sample_cv_data)

        assert response.status_code == 400
        assert "detail" in response.json()

    def test_generate_cv_missing_email(self, client, sample_cv_data):
        """Test CV generation with missing email."""
        sample_cv_data["email"] = "invalid"
        response = client.post("/generate/cv", json=sample_cv_data)

        assert response.status_code == 422  # Pydantic validation error

    def test_generate_cv_missing_competencies(self, client, sample_cv_data):
        """Test CV generation with no competencies."""
        sample_cv_data["competencies"] = []
        response = client.post("/generate/cv", json=sample_cv_data)

        assert response.status_code == 400

    def test_generate_cv_missing_required_fields(self, client):
        """Test CV generation with missing required fields."""
        incomplete_data = {
            "name": "Test User",
            "email": "test@example.com",
            # Missing other required fields
        }
        response = client.post("/generate/cv", json=incomplete_data)

        assert response.status_code == 422  # Pydantic validation error

    def test_generate_cv_with_experience(self, client, sample_cv_data):
        """Test CV generation includes experience section."""
        response = client.post("/generate/cv", json=sample_cv_data)

        assert response.status_code == 200
        assert len(response.content) > 0

    def test_generate_cv_with_education(self, client, sample_cv_data):
        """Test CV generation includes education section."""
        response = client.post("/generate/cv", json=sample_cv_data)

        assert response.status_code == 200
        assert len(response.content) > 0

    def test_generate_cv_with_projects(self, client, sample_cv_data):
        """Test CV generation includes projects section."""
        response = client.post("/generate/cv", json=sample_cv_data)

        assert response.status_code == 200
        assert len(response.content) > 0

    def test_generate_cv_multiple_requests(self, client, sample_cv_data, minimal_cv_data):
        """Test generating CVs for different users."""
        response1 = client.post("/generate/cv", json=sample_cv_data)
        response2 = client.post("/generate/cv", json=minimal_cv_data)

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert len(response1.content) > 0
        assert len(response2.content) > 0
        # Should generate different PDFs
        assert response1.content != response2.content

    def test_generate_cv_long_text_fields(self, client, minimal_cv_data):
        """Test CV with very long text fields."""
        minimal_cv_data["about"] = "A" * 1000  # Long about section
        minimal_cv_data["ikigai"] = "B" * 500

        response = client.post("/generate/cv", json=minimal_cv_data)

        assert response.status_code == 200
        assert len(response.content) > 0

    def test_generate_cv_special_characters_in_name(self, client, minimal_cv_data):
        """Test CV with special characters in name."""
        minimal_cv_data["name"] = "José María Pérez-García"

        response = client.post("/generate/cv", json=minimal_cv_data)

        assert response.status_code == 200
        assert len(response.content) > 0

    def test_generate_cv_response_headers(self, client, sample_cv_data):
        """Test response headers are correct."""
        response = client.post("/generate/cv", json=sample_cv_data)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "content-disposition" in response.headers
        assert "attachment" in response.headers["content-disposition"]
        assert response.headers.get("content-length") or len(response.content) > 0

    def test_generate_cv_malformed_json(self, client):
        """Test with malformed JSON."""
        response = client.post(
            "/generate/cv",
            content="not valid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422

    def test_generate_cv_empty_competency_list(self, client, sample_cv_data):
        """Test with empty competency list."""
        sample_cv_data["competencies"] = []
        response = client.post("/generate/cv", json=sample_cv_data)

        assert response.status_code == 400

    def test_health_check_endpoint(self, client):
        """Test health check endpoint works."""
        response = client.get("/health")

        assert response.status_code == 200
        json_data = response.json()
        assert "status" in json_data
        assert json_data["status"] == "healthy"

    def test_root_endpoint(self, client):
        """Test root endpoint provides info."""
        response = client.get("/")

        assert response.status_code == 200
        json_data = response.json()
        assert "message" in json_data
        assert "endpoints" in json_data
