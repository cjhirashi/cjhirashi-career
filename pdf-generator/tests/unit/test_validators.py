"""Unit tests for Input Validators."""

import pytest
from src.utils.validators import InputValidator


class TestInputValidator:
    """Test Input Validator."""

    def test_validate_cv_data_success(self):
        """Test successful CV data validation."""
        InputValidator.validate_cv_data(
            name="John Doe",
            email="john@example.com",
            phone="+1 555 1234",
            location="New York",
            ikigai="Build great software",
            about="Senior engineer with 10 years of experience",
            competencies=[{"name": "Python", "level": "Expert", "category": "Languages"}],
            experience=[],
            education=[],
            projects=[],
        )
        # If no exception raised, validation passed

    def test_validate_cv_data_empty_name(self):
        """Test CV validation with empty name."""
        with pytest.raises(ValueError, match="Name is required"):
            InputValidator.validate_cv_data(
                name="",
                email="john@example.com",
                phone="+1 555 1234",
                location="New York",
                ikigai="Build great software",
                about="Senior engineer with 10 years of experience",
                competencies=[{"name": "Python", "level": "Expert", "category": "Languages"}],
                experience=[],
                education=[],
                projects=[],
            )

    def test_validate_cv_data_whitespace_only_name(self):
        """Test CV validation with whitespace-only name."""
        with pytest.raises(ValueError, match="Name is required"):
            InputValidator.validate_cv_data(
                name="   ",
                email="john@example.com",
                phone="+1 555 1234",
                location="New York",
                ikigai="Build great software",
                about="Senior engineer with 10 years of experience",
                competencies=[{"name": "Python", "level": "Expert", "category": "Languages"}],
                experience=[],
                education=[],
                projects=[],
            )

    def test_validate_cv_data_invalid_email_no_at(self):
        """Test CV validation with invalid email (no @)."""
        with pytest.raises(ValueError, match="Valid email is required"):
            InputValidator.validate_cv_data(
                name="John Doe",
                email="invalidemail",
                phone="+1 555 1234",
                location="New York",
                ikigai="Build great software",
                about="Senior engineer with 10 years of experience",
                competencies=[{"name": "Python", "level": "Expert", "category": "Languages"}],
                experience=[],
                education=[],
                projects=[],
            )

    def test_validate_cv_data_invalid_email_empty(self):
        """Test CV validation with empty email."""
        with pytest.raises(ValueError, match="Valid email is required"):
            InputValidator.validate_cv_data(
                name="John Doe",
                email="",
                phone="+1 555 1234",
                location="New York",
                ikigai="Build great software",
                about="Senior engineer with 10 years of experience",
                competencies=[{"name": "Python", "level": "Expert", "category": "Languages"}],
                experience=[],
                education=[],
                projects=[],
            )

    def test_validate_cv_data_invalid_phone_too_short(self):
        """Test CV validation with phone number too short."""
        with pytest.raises(ValueError, match="Valid phone number is required"):
            InputValidator.validate_cv_data(
                name="John Doe",
                email="john@example.com",
                phone="123",
                location="New York",
                ikigai="Build great software",
                about="Senior engineer with 10 years of experience",
                competencies=[{"name": "Python", "level": "Expert", "category": "Languages"}],
                experience=[],
                education=[],
                projects=[],
            )

    def test_validate_cv_data_invalid_phone_empty(self):
        """Test CV validation with empty phone."""
        with pytest.raises(ValueError, match="Valid phone number is required"):
            InputValidator.validate_cv_data(
                name="John Doe",
                email="john@example.com",
                phone="",
                location="New York",
                ikigai="Build great software",
                about="Senior engineer with 10 years of experience",
                competencies=[{"name": "Python", "level": "Expert", "category": "Languages"}],
                experience=[],
                education=[],
                projects=[],
            )

    def test_validate_cv_data_empty_location(self):
        """Test CV validation with empty location."""
        with pytest.raises(ValueError, match="Location is required"):
            InputValidator.validate_cv_data(
                name="John Doe",
                email="john@example.com",
                phone="+1 555 1234",
                location="",
                ikigai="Build great software",
                about="Senior engineer with 10 years of experience",
                competencies=[{"name": "Python", "level": "Expert", "category": "Languages"}],
                experience=[],
                education=[],
                projects=[],
            )

    def test_validate_cv_data_ikigai_too_short(self):
        """Test CV validation with ikigai too short."""
        with pytest.raises(ValueError, match="IKIGAI must be at least 10 characters"):
            InputValidator.validate_cv_data(
                name="John Doe",
                email="john@example.com",
                phone="+1 555 1234",
                location="New York",
                ikigai="Short",
                about="Senior engineer with 10 years of experience",
                competencies=[{"name": "Python", "level": "Expert", "category": "Languages"}],
                experience=[],
                education=[],
                projects=[],
            )

    def test_validate_cv_data_about_too_short(self):
        """Test CV validation with about section too short."""
        with pytest.raises(ValueError, match="About section must be at least 20 characters"):
            InputValidator.validate_cv_data(
                name="John Doe",
                email="john@example.com",
                phone="+1 555 1234",
                location="New York",
                ikigai="Build great software",
                about="Short",
                competencies=[{"name": "Python", "level": "Expert", "category": "Languages"}],
                experience=[],
                education=[],
                projects=[],
            )

    def test_validate_cv_data_no_competencies(self):
        """Test CV validation without competencies."""
        with pytest.raises(ValueError, match="At least one competency is required"):
            InputValidator.validate_cv_data(
                name="John Doe",
                email="john@example.com",
                phone="+1 555 1234",
                location="New York",
                ikigai="Build great software",
                about="Senior engineer with 10 years of experience",
                competencies=[],
                experience=[],
                education=[],
                projects=[],
            )

    def test_validate_cv_data_competency_missing_name(self):
        """Test CV validation with competency missing name."""
        with pytest.raises(ValueError, match="Competency name is required"):
            InputValidator.validate_cv_data(
                name="John Doe",
                email="john@example.com",
                phone="+1 555 1234",
                location="New York",
                ikigai="Build great software",
                about="Senior engineer with 10 years of experience",
                competencies=[{"level": "Expert", "category": "Languages"}],
                experience=[],
                education=[],
                projects=[],
            )

    def test_validate_cv_data_competency_missing_level(self):
        """Test CV validation with competency missing level."""
        with pytest.raises(ValueError, match="Competency level is required"):
            InputValidator.validate_cv_data(
                name="John Doe",
                email="john@example.com",
                phone="+1 555 1234",
                location="New York",
                ikigai="Build great software",
                about="Senior engineer with 10 years of experience",
                competencies=[{"name": "Python", "category": "Languages"}],
                experience=[],
                education=[],
                projects=[],
            )

    def test_validate_cv_data_competency_missing_category(self):
        """Test CV validation with competency missing category."""
        with pytest.raises(ValueError, match="Competency category is required"):
            InputValidator.validate_cv_data(
                name="John Doe",
                email="john@example.com",
                phone="+1 555 1234",
                location="New York",
                ikigai="Build great software",
                about="Senior engineer with 10 years of experience",
                competencies=[{"name": "Python", "level": "Expert"}],
                experience=[],
                education=[],
                projects=[],
            )

    def test_validate_cv_data_experience_missing_position(self):
        """Test CV validation with experience missing position."""
        with pytest.raises(ValueError, match="Experience position is required"):
            InputValidator.validate_cv_data(
                name="John Doe",
                email="john@example.com",
                phone="+1 555 1234",
                location="New York",
                ikigai="Build great software",
                about="Senior engineer with 10 years of experience",
                competencies=[{"name": "Python", "level": "Expert", "category": "Languages"}],
                experience=[{"company": "Company", "description": "Long description here"}],
                education=[],
                projects=[],
            )

    def test_validate_cv_data_experience_missing_company(self):
        """Test CV validation with experience missing company."""
        with pytest.raises(ValueError, match="Experience company is required"):
            InputValidator.validate_cv_data(
                name="John Doe",
                email="john@example.com",
                phone="+1 555 1234",
                location="New York",
                ikigai="Build great software",
                about="Senior engineer with 10 years of experience",
                competencies=[{"name": "Python", "level": "Expert", "category": "Languages"}],
                experience=[{"position": "Engineer", "description": "Long description here"}],
                education=[],
                projects=[],
            )

    def test_validate_cv_data_education_missing_degree(self):
        """Test CV validation with education missing degree."""
        with pytest.raises(ValueError, match="Education degree is required"):
            InputValidator.validate_cv_data(
                name="John Doe",
                email="john@example.com",
                phone="+1 555 1234",
                location="New York",
                ikigai="Build great software",
                about="Senior engineer with 10 years of experience",
                competencies=[{"name": "Python", "level": "Expert", "category": "Languages"}],
                experience=[],
                education=[{"school": "MIT", "field": "CS", "year": "2020"}],
                projects=[],
            )

    def test_validate_cv_data_project_missing_name(self):
        """Test CV validation with project missing name."""
        with pytest.raises(ValueError, match="Project name is required"):
            InputValidator.validate_cv_data(
                name="John Doe",
                email="john@example.com",
                phone="+1 555 1234",
                location="New York",
                ikigai="Build great software",
                about="Senior engineer with 10 years of experience",
                competencies=[{"name": "Python", "level": "Expert", "category": "Languages"}],
                experience=[],
                education=[],
                projects=[{"description": "Project description", "technologies": ["Python"]}],
            )

    def test_validate_cover_letter_data_success(self):
        """Test successful Cover Letter data validation."""
        InputValidator.validate_cover_letter_data(
            name="John Doe",
            email="john@example.com",
            date="2024-08-16",
            company_name="Company Inc",
            company_address="123 Main St",
            recipient_name="Hiring Manager",
            position="Engineer",
            body="This is a comprehensive body with sufficient length",
            closing_statement="Thank you for consideration",
            signature="John Doe",
        )
        # If no exception raised, validation passed

    def test_validate_cover_letter_empty_name(self):
        """Test Cover Letter validation with empty name."""
        with pytest.raises(ValueError, match="Name is required"):
            InputValidator.validate_cover_letter_data(
                name="",
                email="john@example.com",
                date="2024-08-16",
                company_name="Company Inc",
                company_address="123 Main St",
                recipient_name="Hiring Manager",
                position="Engineer",
                body="This is a comprehensive body with sufficient length",
                closing_statement="Thank you for consideration",
                signature="John Doe",
            )

    def test_validate_cover_letter_invalid_email(self):
        """Test Cover Letter validation with invalid email."""
        with pytest.raises(ValueError, match="Valid email is required"):
            InputValidator.validate_cover_letter_data(
                name="John Doe",
                email="invalid",
                date="2024-08-16",
                company_name="Company Inc",
                company_address="123 Main St",
                recipient_name="Hiring Manager",
                position="Engineer",
                body="This is a comprehensive body with sufficient length",
                closing_statement="Thank you for consideration",
                signature="John Doe",
            )

    def test_validate_cover_letter_invalid_date_format(self):
        """Test Cover Letter validation with invalid date format."""
        with pytest.raises(ValueError, match="Valid date"):
            InputValidator.validate_cover_letter_data(
                name="John Doe",
                email="john@example.com",
                date="08/16/2024",
                company_name="Company Inc",
                company_address="123 Main St",
                recipient_name="Hiring Manager",
                position="Engineer",
                body="This is a comprehensive body with sufficient length",
                closing_statement="Thank you for consideration",
                signature="John Doe",
            )

    def test_validate_cover_letter_empty_company_name(self):
        """Test Cover Letter validation with empty company name."""
        with pytest.raises(ValueError, match="Company name is required"):
            InputValidator.validate_cover_letter_data(
                name="John Doe",
                email="john@example.com",
                date="2024-08-16",
                company_name="",
                company_address="123 Main St",
                recipient_name="Hiring Manager",
                position="Engineer",
                body="This is a comprehensive body with sufficient length",
                closing_statement="Thank you for consideration",
                signature="John Doe",
            )

    def test_validate_cover_letter_body_too_short(self):
        """Test Cover Letter validation with body too short."""
        with pytest.raises(ValueError, match="Letter body must be at least 50 characters"):
            InputValidator.validate_cover_letter_data(
                name="John Doe",
                email="john@example.com",
                date="2024-08-16",
                company_name="Company Inc",
                company_address="123 Main St",
                recipient_name="Hiring Manager",
                position="Engineer",
                body="Too short",
                closing_statement="Thank you for consideration",
                signature="John Doe",
            )

    def test_validate_cover_letter_closing_statement_too_short(self):
        """Test Cover Letter validation with closing statement too short."""
        with pytest.raises(ValueError, match="Closing statement must be at least 10 characters"):
            InputValidator.validate_cover_letter_data(
                name="John Doe",
                email="john@example.com",
                date="2024-08-16",
                company_name="Company Inc",
                company_address="123 Main St",
                recipient_name="Hiring Manager",
                position="Engineer",
                body="This is a comprehensive body with sufficient length",
                closing_statement="Short",
                signature="John Doe",
            )

    def test_validate_cover_letter_empty_signature(self):
        """Test Cover Letter validation with empty signature."""
        with pytest.raises(ValueError, match="Signature is required"):
            InputValidator.validate_cover_letter_data(
                name="John Doe",
                email="john@example.com",
                date="2024-08-16",
                company_name="Company Inc",
                company_address="123 Main St",
                recipient_name="Hiring Manager",
                position="Engineer",
                body="This is a comprehensive body with sufficient length",
                closing_statement="Thank you for consideration",
                signature="",
            )

    def test_sanitize_text_normal(self):
        """Test text sanitization with normal text."""
        text = "This is normal text"
        result = InputValidator.sanitize_text(text)
        assert result == "This is normal text"

    def test_sanitize_text_with_pdf_injection_chars(self):
        """Test text sanitization removes PDF injection characters."""
        text = "Normal text <<injection>> more text"
        result = InputValidator.sanitize_text(text)
        assert "<<" not in result
        assert ">>" not in result
        assert "injection" in result

    def test_sanitize_text_empty_string(self):
        """Test text sanitization with empty string."""
        result = InputValidator.sanitize_text("")
        assert result == ""

    def test_sanitize_text_none_input(self):
        """Test text sanitization with None input."""
        result = InputValidator.sanitize_text(None)
        assert result == ""

    def test_sanitize_text_with_whitespace(self):
        """Test text sanitization trims whitespace."""
        text = "  Text with spaces  "
        result = InputValidator.sanitize_text(text)
        assert result == "Text with spaces"

    def test_sanitize_text_with_special_characters(self):
        """Test text sanitization preserves special characters (except PDF injection)."""
        text = "Email: test@example.com, Phone: +1-555-1234"
        result = InputValidator.sanitize_text(text)
        assert "@" in result
        assert "+" in result
        assert "-" in result
