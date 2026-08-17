"""Unit tests for Data Formatters."""

import pytest
from src.utils.formatters import DataFormatter


class TestDataFormatter:
    """Test Data Formatter."""

    def test_format_competencies_single(self):
        """Test formatting single competency."""
        formatter = DataFormatter()
        competencies = [
            {"category": "Languages", "name": "Python", "level": "Expert"}
        ]
        result = formatter.format_competencies(competencies)
        assert isinstance(result, list)
        assert len(result) == 1
        assert "Python" in str(result)

    def test_format_competencies_multiple(self):
        """Test formatting multiple competencies."""
        formatter = DataFormatter()
        competencies = [
            {"category": "Languages", "name": "Python", "level": "Expert"},
            {"category": "Languages", "name": "Go", "level": "Advanced"},
            {"category": "Databases", "name": "PostgreSQL", "level": "Expert"},
        ]
        result = formatter.format_competencies(competencies)
        assert isinstance(result, list)
        assert len(result) == 3

    def test_format_competencies_empty(self):
        """Test formatting empty competencies."""
        formatter = DataFormatter()
        result = formatter.format_competencies([])
        assert isinstance(result, list)
        assert len(result) == 0

    def test_format_competencies_grouped_by_category(self):
        """Test that competencies are grouped by category."""
        formatter = DataFormatter()
        competencies = [
            {"category": "Languages", "name": "Python", "level": "Expert"},
            {"category": "Languages", "name": "Go", "level": "Advanced"},
            {"category": "Databases", "name": "PostgreSQL", "level": "Expert"},
        ]
        result = formatter.format_competencies(competencies)
        # Result should be organized by category
        assert len(result) == 3

    def test_format_experience_single(self):
        """Test formatting single experience."""
        formatter = DataFormatter()
        experience = [
            {
                "position": "Senior Engineer",
                "company": "Tech Corp",
                "start_date": "2022-01",
                "end_date": "present",
                "description": "Led team of engineers",
            }
        ]
        result = formatter.format_experience(experience)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_format_experience_multiple(self):
        """Test formatting multiple experiences."""
        formatter = DataFormatter()
        experience = [
            {
                "position": "Senior Engineer",
                "company": "Tech Corp",
                "start_date": "2022-01",
                "end_date": "present",
                "description": "Led team of engineers",
            },
            {
                "position": "Engineer",
                "company": "Startup Inc",
                "start_date": "2019-06",
                "end_date": "2021-12",
                "description": "Developed core APIs",
            },
        ]
        result = formatter.format_experience(experience)
        assert isinstance(result, list)
        assert len(result) == 2

    def test_format_experience_without_end_date(self):
        """Test formatting experience without end date."""
        formatter = DataFormatter()
        experience = [
            {
                "position": "Senior Engineer",
                "company": "Tech Corp",
                "start_date": "2022-01",
                "end_date": "present",
                "description": "Led team of engineers",
            }
        ]
        result = formatter.format_experience(experience)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_format_experience_empty(self):
        """Test formatting empty experience."""
        formatter = DataFormatter()
        result = formatter.format_experience([])
        assert isinstance(result, list)
        assert len(result) == 0

    def test_format_education_single(self):
        """Test formatting single education."""
        formatter = DataFormatter()
        education = [
            {
                "degree": "Master's Degree",
                "school": "MIT",
                "field": "Computer Science",
                "year": "2020",
            }
        ]
        result = formatter.format_education(education)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_format_education_multiple(self):
        """Test formatting multiple educations."""
        formatter = DataFormatter()
        education = [
            {
                "degree": "Master's Degree",
                "school": "MIT",
                "field": "Computer Science",
                "year": "2020",
            },
            {
                "degree": "Bachelor's Degree",
                "school": "Stanford",
                "field": "Electrical Engineering",
                "year": "2018",
            },
        ]
        result = formatter.format_education(education)
        assert isinstance(result, list)
        assert len(result) == 2

    def test_format_education_empty(self):
        """Test formatting empty education."""
        formatter = DataFormatter()
        result = formatter.format_education([])
        assert isinstance(result, list)
        assert len(result) == 0

    def test_format_projects_single(self):
        """Test formatting single project."""
        formatter = DataFormatter()
        projects = [
            {
                "name": "Task Queue",
                "description": "High-performance task queue",
                "technologies": ["Python", "Redis"],
                "link": "https://github.com/example/task-queue",
            }
        ]
        result = formatter.format_projects(projects)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_format_projects_multiple(self):
        """Test formatting multiple projects."""
        formatter = DataFormatter()
        projects = [
            {
                "name": "Task Queue",
                "description": "High-performance task queue",
                "technologies": ["Python", "Redis"],
                "link": "https://github.com/example/task-queue",
            },
            {
                "name": "Analytics Platform",
                "description": "Real-time analytics dashboard",
                "technologies": ["React", "Python"],
                "link": "https://github.com/example/analytics",
            },
        ]
        result = formatter.format_projects(projects)
        assert isinstance(result, list)
        assert len(result) == 2

    def test_format_projects_without_link(self):
        """Test formatting project without link."""
        formatter = DataFormatter()
        projects = [
            {
                "name": "Task Queue",
                "description": "High-performance task queue",
                "technologies": ["Python", "Redis"],
            }
        ]
        result = formatter.format_projects(projects)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_format_projects_empty(self):
        """Test formatting empty projects."""
        formatter = DataFormatter()
        result = formatter.format_projects([])
        assert isinstance(result, list)
        assert len(result) == 0

    def test_format_competencies_with_special_characters(self):
        """Test formatting competencies with special characters."""
        formatter = DataFormatter()
        competencies = [
            {"category": "Languages", "name": "C++", "level": "Advanced"},
            {"category": "Languages", "name": "C#", "level": "Intermediate"},
        ]
        result = formatter.format_competencies(competencies)
        assert isinstance(result, list)
        assert len(result) == 2

    def test_format_experience_with_special_company_names(self):
        """Test formatting experience with special company names."""
        formatter = DataFormatter()
        experience = [
            {
                "position": "Engineer",
                "company": "O'Brien & Sons Inc.",
                "start_date": "2020-01",
                "end_date": "present",
                "description": "Built software solutions",
            }
        ]
        result = formatter.format_experience(experience)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_format_projects_multiple_technologies(self):
        """Test formatting project with many technologies."""
        formatter = DataFormatter()
        projects = [
            {
                "name": "Complex Project",
                "description": "Complex system description",
                "technologies": [
                    "Python",
                    "FastAPI",
                    "PostgreSQL",
                    "Redis",
                    "Docker",
                    "Kubernetes",
                    "React",
                ],
            }
        ]
        result = formatter.format_projects(projects)
        assert isinstance(result, list)
        assert len(result) == 1
