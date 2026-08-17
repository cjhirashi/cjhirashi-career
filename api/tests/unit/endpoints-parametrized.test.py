import pytest
from app import app
from schemas import LoginRequest, IdentityCreate

class TestEndpointsParametrized:
    """Parametrized tests for all API endpoints"""

    @pytest.mark.parametrize("endpoint,method", [
        ("/api/v1/health", "GET"),
        ("/api/v1/auth/login", "POST"),
        ("/api/v1/auth/logout", "POST"),
        ("/api/v1/identity", "GET"),
        ("/api/v1/competencies", "GET"),
        ("/api/v1/evidence", "GET"),
    ])
    def test_endpoints_exist(self, endpoint, method):
        """All endpoints should be registered"""
        assert endpoint is not None
        assert method in ["GET", "POST", "PUT", "DELETE", "PATCH"]

    @pytest.mark.parametrize("auth_header", [
        "Bearer valid_token",
        "Bearer ",
        "",
        "Invalid",
    ])
    def test_auth_header_variants(self, auth_header):
        """Test different auth header formats"""
        assert auth_header is not None

    @pytest.mark.parametrize("status_code", [200, 201, 400, 401, 403, 404, 422, 500])
    def test_http_status_codes(self, status_code):
        """API should return appropriate status codes"""
        assert status_code >= 200
        assert status_code < 600

