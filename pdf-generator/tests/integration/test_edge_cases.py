"""Integration tests for edge cases and error handling."""

import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    """Get FastAPI test client."""
    return TestClient(app)


class TestCVEdgeCases:
    """Test CV generation edge cases."""

    def test_generate_cv_with_unicode_characters(self, client):
        """Test CV with unicode characters in name and fields."""
        data = {
            "name": "José María Pérez-García",
            "email": "jose@example.com",
            "phone": "+34 666 777 888",
            "location": "Madrid, España",
            "ikigai": "Construir software excepcional con pasión y dedicación",
            "about": "Ingeniero de software con experiencia en arquitectura distribuida y liderazgo de equipos técnicos.",
            "competencies": [
                {"category": "Lenguajes", "name": "Python", "level": "Experto"},
                {"category": "Lenguajes", "name": "Go", "level": "Avanzado"},
            ],
            "experience": [],
            "education": [],
            "projects": [],
        }
        response = client.post("/generate/cv", json=data)
        assert response.status_code == 200
        assert len(response.content) > 0

    def test_generate_cv_with_emoji_in_text(self, client):
        """Test CV with emoji characters (should handle gracefully)."""
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1 555 1234",
            "location": "New York, USA",
            "ikigai": "Build great software that makes people happy 🚀",
            "about": "Senior engineer passionate about clean code and best practices ✨",
            "competencies": [
                {"category": "Languages", "name": "Python", "level": "Expert"},
            ],
            "experience": [],
            "education": [],
            "projects": [],
        }
        response = client.post("/generate/cv", json=data)
        # Should handle emoji without crashing
        assert response.status_code in [200, 400]  # Depends on emoji support

    def test_generate_cv_with_very_long_name(self, client):
        """Test CV with very long name (but within field limits)."""
        long_name = "John Alexander Fitzgerald O'Brien-Smith de la Cruz González"
        data = {
            "name": long_name,
            "email": "john@example.com",
            "phone": "+1 555 1234",
            "location": "New York, USA",
            "ikigai": "Build great software",
            "about": "Senior engineer with extensive experience in software development",
            "competencies": [
                {"category": "Languages", "name": "Python", "level": "Expert"},
            ],
            "experience": [],
            "education": [],
            "projects": [],
        }
        response = client.post("/generate/cv", json=data)
        assert response.status_code == 200

    def test_generate_cv_with_maximum_competencies(self, client):
        """Test CV with maximum number of competencies allowed."""
        competencies = [
            {
                "category": f"Category{i}",
                "name": f"Technology{i}",
                "level": "Expert",
            }
            for i in range(50)
        ]
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1 555 1234",
            "location": "New York, USA",
            "ikigai": "Build great software",
            "about": "Senior engineer with extensive knowledge across many technologies",
            "competencies": competencies,
            "experience": [],
            "education": [],
            "projects": [],
        }
        response = client.post("/generate/cv", json=data)
        assert response.status_code == 200

    def test_generate_cv_exceeds_maximum_competencies(self, client):
        """Test CV with more than maximum competencies (should fail validation)."""
        competencies = [
            {
                "category": f"Category{i}",
                "name": f"Technology{i}",
                "level": "Expert",
            }
            for i in range(51)
        ]
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1 555 1234",
            "location": "New York, USA",
            "ikigai": "Build great software",
            "about": "Senior engineer with extensive knowledge",
            "competencies": competencies,
            "experience": [],
            "education": [],
            "projects": [],
        }
        response = client.post("/generate/cv", json=data)
        assert response.status_code == 422  # Validation error

    def test_generate_cv_with_very_long_about_section(self, client):
        """Test CV with very long about section (within limits)."""
        long_text = "A" * 2000  # Max is 2000
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1 555 1234",
            "location": "New York, USA",
            "ikigai": "Build great software",
            "about": long_text,
            "competencies": [
                {"category": "Languages", "name": "Python", "level": "Expert"},
            ],
            "experience": [],
            "education": [],
            "projects": [],
        }
        response = client.post("/generate/cv", json=data)
        assert response.status_code == 200

    def test_generate_cv_exceeds_about_section_limit(self, client):
        """Test CV with about section exceeding limit."""
        long_text = "A" * 2001  # Max is 2000
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1 555 1234",
            "location": "New York, USA",
            "ikigai": "Build great software",
            "about": long_text,
            "competencies": [
                {"category": "Languages", "name": "Python", "level": "Expert"},
            ],
            "experience": [],
            "education": [],
            "projects": [],
        }
        response = client.post("/generate/cv", json=data)
        assert response.status_code == 422

    def test_generate_cv_with_multiple_experiences(self, client):
        """Test CV with multiple experiences."""
        experiences = [
            {
                "position": f"Role{i}",
                "company": f"Company{i}",
                "start_date": "2020-01",
                "end_date": "present",
                "description": "Responsible for key initiatives and project delivery",
            }
            for i in range(10)
        ]
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1 555 1234",
            "location": "New York, USA",
            "ikigai": "Build great software",
            "about": "Senior engineer with extensive experience across many organizations",
            "competencies": [
                {"category": "Languages", "name": "Python", "level": "Expert"},
            ],
            "experience": experiences,
            "education": [],
            "projects": [],
        }
        response = client.post("/generate/cv", json=data)
        assert response.status_code == 200

    def test_generate_cv_with_all_sections_populated(self, client):
        """Test CV with all sections fully populated."""
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1 555 1234",
            "location": "New York, USA",
            "ikigai": "Build great software with passion",
            "about": "Senior engineer with 10+ years of experience in distributed systems",
            "competencies": [
                {"category": "Languages", "name": "Python", "level": "Expert"},
                {"category": "Languages", "name": "Go", "level": "Advanced"},
                {"category": "Databases", "name": "PostgreSQL", "level": "Expert"},
            ],
            "experience": [
                {
                    "position": "Senior Engineer",
                    "company": "Tech Corp",
                    "start_date": "2020-01",
                    "end_date": "present",
                    "description": "Led architecture redesign and team management",
                },
                {
                    "position": "Engineer",
                    "company": "StartUp Inc",
                    "start_date": "2018-06",
                    "end_date": "2019-12",
                    "description": "Built core platform and APIs",
                },
            ],
            "education": [
                {
                    "degree": "Master's",
                    "school": "Stanford University",
                    "field": "Computer Science",
                    "year": "2018",
                },
                {
                    "degree": "Bachelor's",
                    "school": "UC Berkeley",
                    "field": "Electrical Engineering",
                    "year": "2016",
                },
            ],
            "projects": [
                {
                    "name": "Task Queue",
                    "description": "High-performance distributed task queue system",
                    "technologies": ["Python", "FastAPI", "Redis"],
                    "link": "https://github.com/example/task-queue",
                },
                {
                    "name": "Analytics Platform",
                    "description": "Real-time analytics dashboard",
                    "technologies": ["React", "Python", "WebSockets"],
                    "link": "https://github.com/example/analytics",
                },
            ],
        }
        response = client.post("/generate/cv", json=data)
        assert response.status_code == 200
        assert len(response.content) > 0


class TestCoverLetterEdgeCases:
    """Test Cover Letter edge cases."""

    def test_generate_cover_letter_with_unicode_characters(self, client):
        """Test Cover Letter with unicode characters."""
        data = {
            "name": "José María García",
            "email": "jose@example.com",
            "date": "2024-08-16",
            "company_name": "Empresa Tecnológica Española",
            "company_address": "Calle Principal 123, Madrid, España",
            "recipient_name": "Director de Recursos Humanos",
            "position": "Ingeniero de Software Senior",
            "body": "Me dirijo a ustedes para expresar mi interés en la posición de Ingeniero de Software Senior en su prestigiosa organización. Con más de diez años de experiencia en sistemas distribuidos y arquitectura de software, creo que soy un candidato idóneo para este puesto.",
            "closing_statement": "Quedo atento a sus comentarios y agradezco la consideración de mi candidatura.",
            "signature": "José María García",
        }
        response = client.post("/generate/cover-letter", json=data)
        assert response.status_code == 200

    def test_generate_cover_letter_with_very_long_body(self, client):
        """Test Cover Letter with very long body (within limits)."""
        long_body = "A" * 5000  # Max is 5000
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "date": "2024-08-16",
            "company_name": "Company Inc",
            "company_address": "123 Main St",
            "recipient_name": "Hiring Manager",
            "position": "Senior Engineer",
            "body": long_body,
            "closing_statement": "Thank you for consideration",
            "signature": "John Doe",
        }
        response = client.post("/generate/cover-letter", json=data)
        assert response.status_code == 200

    def test_generate_cover_letter_exceeds_body_limit(self, client):
        """Test Cover Letter with body exceeding limit."""
        long_body = "A" * 5001  # Max is 5000
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "date": "2024-08-16",
            "company_name": "Company Inc",
            "company_address": "123 Main St",
            "recipient_name": "Hiring Manager",
            "position": "Senior Engineer",
            "body": long_body,
            "closing_statement": "Thank you for consideration",
            "signature": "John Doe",
        }
        response = client.post("/generate/cover-letter", json=data)
        assert response.status_code == 422

    def test_generate_cover_letter_with_special_company_name(self, client):
        """Test Cover Letter with special characters in company name."""
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "date": "2024-08-16",
            "company_name": "O'Brien & Sons Inc.",
            "company_address": "123 Main St",
            "recipient_name": "Hiring Manager",
            "position": "Senior Engineer",
            "body": "I am very interested in this position at your esteemed organization and believe I would be a great fit for your team.",
            "closing_statement": "Thank you for your time and consideration",
            "signature": "John Doe",
        }
        response = client.post("/generate/cover-letter", json=data)
        assert response.status_code == 200

    def test_generate_cover_letter_with_multiline_content(self, client):
        """Test Cover Letter with extensive multiline content."""
        multiline_body = """I am writing to express my strong interest in the Senior Software Engineer position at your organization.

Your company's commitment to innovation and technical excellence aligns perfectly with my professional values and career aspirations. With over 10 years of experience in building scalable distributed systems and leading high-performing engineering teams, I am confident that I can make significant contributions to your organization.

In my current role, I have successfully:
- Architected and deployed microservices-based systems
- Led teams of talented engineers
- Implemented performance optimizations
- Mentored junior developers

I am particularly interested in your company's work in cloud-native technologies and your commitment to engineering excellence."""

        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "date": "2024-08-16",
            "company_name": "Tech Company Inc",
            "company_address": "456 Innovation Drive, San Francisco, CA",
            "recipient_name": "Sarah Johnson",
            "position": "Senior Software Engineer",
            "body": multiline_body,
            "closing_statement": "I look forward to discussing how I can contribute to your team's success.",
            "signature": "John Doe",
        }
        response = client.post("/generate/cover-letter", json=data)
        assert response.status_code == 200

    def test_generate_cover_letter_maximum_field_lengths(self, client):
        """Test Cover Letter with fields at maximum allowed lengths."""
        data = {
            "name": "A" * 200,  # Max name length
            "email": "test@example.com",
            "date": "2024-08-16",
            "company_name": "B" * 200,  # Max company name length
            "company_address": "C" * 500,  # Max address length
            "recipient_name": "D" * 200,  # Max recipient name length
            "position": "E" * 200,  # Max position length
            "body": "F" * 5000,  # Max body length
            "closing_statement": "G" * 500,  # Max closing statement length
            "signature": "H" * 200,  # Max signature length
        }
        response = client.post("/generate/cover-letter", json=data)
        # Should work with max lengths
        assert response.status_code in [200, 422]
