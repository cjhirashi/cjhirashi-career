"""Alcance de metodologías a agentes y validación de agent_profile_ids."""
import pytest
from pydantic import ValidationError

from services.methodology_scope import applies_to_agent
from services.bedrock.agent_profiles import AGENT_METHODOLOGIES, AGENT_PDF_DESIGN, known_agent_profile_ids
from schemas.career_methodologies import OperationalMethodologyCreate


def test_applies_to_all_when_empty():
    assert applies_to_agent(None, AGENT_PDF_DESIGN)
    assert applies_to_agent([], AGENT_PDF_DESIGN)


def test_applies_only_to_listed_agents():
    ids = [AGENT_PDF_DESIGN]
    assert applies_to_agent(ids, AGENT_PDF_DESIGN)
    assert not applies_to_agent(ids, "agent_search_operations")


def test_methodologies_guardian_sees_all():
    assert applies_to_agent(["agent_pdf_design"], AGENT_METHODOLOGIES)


def test_known_agent_ids_include_web_and_github():
    known = known_agent_profile_ids()
    assert "agent_web_search" in known
    assert "agent_github" in known


def test_schema_accepts_known_ids():
    row = OperationalMethodologyCreate(
        title="Diseño PDF",
        content="# h",
        agent_profile_ids=["agent_pdf_design", "agent_pdf_render"],
    )
    assert row.agent_profile_ids == ["agent_pdf_design", "agent_pdf_render"]


def test_schema_rejects_unknown_ids():
    with pytest.raises(ValidationError):
        OperationalMethodologyCreate(
            title="X",
            content="# h",
            agent_profile_ids=["not_an_agent"],
        )
