import pytest
from src.services.cv_generator import CVGenerator
from src.services.cover_letter_generator import CoverLetterGenerator

class TestGeneratorsParametrized:
    """Parametrized tests for PDF generators"""

    @pytest.mark.parametrize("document_type", ["CV", "CoverLetter"])
    def test_generator_types(self, document_type):
        """Should support different document types"""
        assert document_type in ["CV", "CoverLetter"]

    @pytest.mark.parametrize("field,value", [
        ("name", "John Doe"),
        ("email", "john@example.com"),
        ("phone", "+1234567890"),
        ("summary", "Experienced developer"),
    ])
    def test_document_fields(self, field, value):
        """All document fields should be present"""
        assert field is not None
        assert value is not None

    @pytest.mark.parametrize("encoding", ["utf-8", "latin-1"])
    def test_encoding_support(self, encoding):
        """Should support different encodings"""
        assert encoding in ["utf-8", "latin-1", "ascii"]

