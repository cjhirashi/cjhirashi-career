"""
Unit tests para utilidades (constants, helpers, etc).
"""
import pytest
from utils.constants import (
    COMPETENCY_TYPES, COMPETENCY_LEVELS, EMPLOYMENT_TYPES,
    INTERVIEW_TYPES, INTERVIEW_ROUNDS, RELATIONSHIP_TYPES
)


class TestConstants:
    """Tests para constantes definidas."""

    def test_competency_types_exist(self):
        """Verificar que tipos de competencia están definidos."""
        assert "técnica" in COMPETENCY_TYPES
        assert "transferible" in COMPETENCY_TYPES
        assert "negocio" in COMPETENCY_TYPES
        assert len(COMPETENCY_TYPES) >= 3

    def test_competency_levels_exist(self):
        """Verificar que niveles de competencia están definidos."""
        assert "Beginner" in COMPETENCY_LEVELS
        assert "Intermediate" in COMPETENCY_LEVELS
        assert "Advanced" in COMPETENCY_LEVELS
        assert "Expert" in COMPETENCY_LEVELS
        assert len(COMPETENCY_LEVELS) >= 4

    def test_employment_types_exist(self):
        """Verificar que tipos de empleo están definidos."""
        assert "full-time" in EMPLOYMENT_TYPES
        assert "part-time" in EMPLOYMENT_TYPES
        assert "contract" in EMPLOYMENT_TYPES
        assert len(EMPLOYMENT_TYPES) >= 3

    def test_interview_types_exist(self):
        """Verificar que tipos de entrevista están definidos."""
        assert "phone" in INTERVIEW_TYPES
        assert "video" in INTERVIEW_TYPES
        assert "technical" in INTERVIEW_TYPES
        assert len(INTERVIEW_TYPES) >= 3

    def test_interview_rounds_exist(self):
        """Verificar que rondas de entrevista están definidas."""
        assert "round_1" in INTERVIEW_ROUNDS or "screening" in INTERVIEW_ROUNDS
        assert len(INTERVIEW_ROUNDS) >= 2

    def test_relationship_types_exist(self):
        """Verificar que tipos de relación están definidos."""
        assert "mentor" in RELATIONSHIP_TYPES or "professional" in RELATIONSHIP_TYPES
        assert len(RELATIONSHIP_TYPES) >= 2

    def test_constants_are_lists_or_tuples(self):
        """Verificar que constantes son iterables."""
        assert isinstance(COMPETENCY_TYPES, (list, tuple))
        assert isinstance(COMPETENCY_LEVELS, (list, tuple))
        assert isinstance(EMPLOYMENT_TYPES, (list, tuple))
        assert isinstance(INTERVIEW_TYPES, (list, tuple))
        assert isinstance(INTERVIEW_ROUNDS, (list, tuple))
        assert isinstance(RELATIONSHIP_TYPES, (list, tuple))

    def test_no_empty_constants(self):
        """Verificar que no hay constantes vacías."""
        assert len(COMPETENCY_TYPES) > 0
        assert len(COMPETENCY_LEVELS) > 0
        assert len(EMPLOYMENT_TYPES) > 0
        assert len(INTERVIEW_TYPES) > 0
        assert len(INTERVIEW_ROUNDS) > 0
        assert len(RELATIONSHIP_TYPES) > 0
