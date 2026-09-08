"""Sección ↔ agente L2: unión de herramientas y metodologías de sección (spec 004).

RF-002 (derived_tools_for_agent = unión de sus secciones) y RF-005/006
(set_section_methodologies edita operational_methodologies.section_ids).
"""
from unittest.mock import AsyncMock, patch

import pytest

from services import section_catalog


@pytest.mark.asyncio
@pytest.mark.requisito("RF-002")
async def test_derived_tools_for_agent_is_union_of_its_sections():
    # L2 que posee sec-32 (tabla projects) y sec-6 (funcional LinkedIn)
    async def fake_sections_for_agent(db, profile_id):
        return [{"id": "sec-32"}, {"id": "sec-6"}]

    with patch.object(section_catalog, "sections_for_agent", new=fake_sections_for_agent):
        tools = await section_catalog.derived_tools_for_agent(db=None, profile_id="agent_professional_identity")

    from services.admin_sections import get_section_spec, tools_for_section

    expected = tools_for_section(get_section_spec("sec-32")) | tools_for_section(get_section_spec("sec-6"))
    assert tools == expected
    assert "list_career_record" in tools  # de sec-32
    assert "get_linkedin_status" in tools  # de sec-6


@pytest.mark.asyncio
@pytest.mark.requisito("RF-002")
async def test_derived_tools_for_agent_single_section():
    async def fake_sections_for_agent(db, profile_id):
        return [{"id": "sec-32"}]

    with patch.object(section_catalog, "sections_for_agent", new=fake_sections_for_agent):
        tools = await section_catalog.derived_tools_for_agent(db=None, profile_id="x")

    from services.admin_sections import get_section_spec, tools_for_section

    assert tools == tools_for_section(get_section_spec("sec-32"))


@pytest.mark.asyncio
@pytest.mark.requisito("RF-002")
async def test_derived_tools_for_agent_no_sections_is_empty():
    async def fake_sections_for_agent(db, profile_id):
        return []

    with patch.object(section_catalog, "sections_for_agent", new=fake_sections_for_agent):
        assert await section_catalog.derived_tools_for_agent(db=None, profile_id="x") == set()


# ============================================================================
# RF-005 / RF-006 — metodologías ligadas a una sección
# ============================================================================


class _Meth:
    def __init__(self, mid, section_ids=None):
        self.id = mid
        self.section_ids = section_ids


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        rows = self._rows
        class _S:
            def all(_self):
                return rows
        return _S()

    def all(self):
        return list(self._rows)


class _DB:
    def __init__(self, rows):
        self._rows = rows

    async def execute(self, *a, **k):
        return _Result(self._rows)


@pytest.mark.asyncio
@pytest.mark.requisito("RF-005")
async def test_set_section_methodologies_links_and_unlinks():
    rows = [_Meth("opm-1", ["sec-9"]), _Meth("opm-2", None), _Meth("opm-3", ["sec-5"])]
    updates = {}

    async def fake_update(self, db, uid, item_id, data):
        updates[item_id] = data["section_ids"]
        # reflejar en el objeto para section_methodology_ids posterior
        for m in rows:
            if m.id == item_id:
                m.section_ids = data["section_ids"]

    with patch("repositories.career_repository.CareerRepository.update_for_user", new=fake_update), patch(
        "repositories.career_repository.CareerRepository.reindex_for_user", new=AsyncMock(return_value=0)
    ):
        # ligar opm-1 y opm-2 a sec-5; opm-3 (que ya tenía sec-5) se desliga
        await section_catalog.set_section_methodologies(_DB(rows), "usr-2", "sec-5", ["opm-1", "opm-2"])

    assert set(updates["opm-1"]) == {"sec-5", "sec-9"}  # añade, conserva sec-9
    assert updates["opm-2"] == ["sec-5"]
    assert updates["opm-3"] == []  # se quitó sec-5


@pytest.mark.asyncio
@pytest.mark.requisito("RF-006")
async def test_set_section_methodologies_rejects_unknown_ids():
    rows = [_Meth("opm-1", None)]
    with pytest.raises(ValueError):
        await section_catalog.set_section_methodologies(_DB(rows), "usr-2", "sec-5", ["opm-999"])
    with pytest.raises(KeyError):
        await section_catalog.set_section_methodologies(_DB(rows), "usr-2", "sec-nope", ["opm-1"])
