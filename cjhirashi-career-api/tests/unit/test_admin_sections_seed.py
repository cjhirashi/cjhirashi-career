"""Seeder idempotente de la jerarquía de secciones del Admin (ADR-022)."""
import pytest
from sqlalchemy import func, select

from models.admin_section_group import AdminSectionGroup
from models.admin_section_l1 import AdminSectionL1
from models.admin_view import AdminView
from services.admin_sections import list_section_specs
from services.admin_sections_seed import (
    VIEW_ID_MAP,
    _L3_CHAT_FALLBACK,
    sync_structure,
)
from services.bedrock.agent_profiles import get_profile


async def _count(session, model):
    return (await session.execute(select(func.count()).select_from(model))).scalar()


async def test_seed_creates_full_structure(hier_db):
    assert await _count(hier_db, AdminSectionGroup) == 11
    assert await _count(hier_db, AdminSectionL1) == 54
    assert await _count(hier_db, AdminView) == len(VIEW_ID_MAP) == 123


async def test_seed_never_writes_operator_columns(hier_db):
    rows = (await hier_db.execute(select(AdminView))).scalars().all()
    assert all(r.responsible_agent_profile_id is None for r in rows)
    assert all(r.instructions is None for r in rows)
    assert all(r.origin == "code" for r in rows)


async def test_seed_is_idempotent(hier_session_factory):
    async with hier_session_factory() as s:
        await sync_structure(s)
        await s.commit()
    async with hier_session_factory() as s:
        await sync_structure(s)
        await s.commit()
    async with hier_session_factory() as s:
        assert await _count(s, AdminView) == 123
        assert await _count(s, AdminSectionL1) == 54


async def test_seed_preserves_operator_sort_order_and_group(hier_session_factory):
    async with hier_session_factory() as s:
        await sync_structure(s)
        await s.commit()
    async with hier_session_factory() as s:
        row = (
            await s.execute(select(AdminSectionL1).where(AdminSectionL1.system_name == "dashboard"))
        ).scalar_one()
        row.sort_order = 999
        grp = (
            await s.execute(
                select(AdminSectionGroup).where(AdminSectionGroup.system_name == "settings")
            )
        ).scalar_one()
        row.group_id = grp.id
        await s.commit()
    async with hier_session_factory() as s:
        await sync_structure(s)
        await s.commit()
    async with hier_session_factory() as s:
        row = (
            await s.execute(select(AdminSectionL1).where(AdminSectionL1.system_name == "dashboard"))
        ).scalar_one()
        assert row.sort_order == 999  # insert-only: el seeder no lo pisa
        grp = (
            await s.execute(
                select(AdminSectionGroup).where(AdminSectionGroup.system_name == "settings")
            )
        ).scalar_one()
        assert row.group_id == grp.id
        assert row.label == "Dashboard"  # label sí se refresca


async def test_seed_prunes_orphan_code_rows(hier_session_factory):
    async with hier_session_factory() as s:
        await sync_structure(s)
        await s.commit()
    async with hier_session_factory() as s:
        grp = (await s.execute(select(AdminSectionGroup).limit(1))).scalar_one()
        s.add(
            AdminSectionL1(
                id="s1-9000",
                group_id=grp.id,
                system_name="ghost-section",
                label="Ghost",
                path="/ghost",
                section_type="table",
                sort_order=0,
                origin="code",
            )
        )
        await s.flush()
        s.add(
            AdminView(
                id="vw-9000",
                owner_l1_id="s1-9000",
                key="list",
                label="Lista",
                sort_order=0,
                data_source="crud",
                resource_key=None,
                origin="code",
            )
        )
        await s.commit()
    async with hier_session_factory() as s:
        await sync_structure(s)
        await s.commit()
    async with hier_session_factory() as s:
        assert (
            await s.execute(select(AdminSectionL1).where(AdminSectionL1.id == "s1-9000"))
        ).scalar_one_or_none() is None
        # CASCADE arrastró la vista huérfana
        assert (
            await s.execute(select(AdminView).where(AdminView.id == "vw-9000"))
        ).scalar_one_or_none() is None


async def test_seed_does_not_prune_admin_owned_rows(hier_session_factory):
    async with hier_session_factory() as s:
        await sync_structure(s)
        await s.commit()
    async with hier_session_factory() as s:
        grp = (await s.execute(select(AdminSectionGroup).limit(1))).scalar_one()
        s.add(
            AdminSectionL1(
                id="s1-8000",
                group_id=grp.id,
                system_name="operator-section",
                label="Operador",
                path="/operator",
                section_type="table",
                sort_order=0,
                origin="admin",
            )
        )
        await s.commit()
    async with hier_session_factory() as s:
        await sync_structure(s)
        await s.commit()
    async with hier_session_factory() as s:
        assert (
            await s.execute(select(AdminSectionL1).where(AdminSectionL1.id == "s1-8000"))
        ).scalar_one_or_none() is not None


def test_l3_chat_fallback_resolves_to_l2_or_nothing():
    for source, target in _L3_CHAT_FALLBACK.items():
        assert get_profile(source).level == 3
        assert get_profile(target).level in (1, 2)


def test_view_id_map_is_contiguous_and_covers_registry():
    ids = sorted(int(v.split("-")[1]) for v in VIEW_ID_MAP.values())
    assert ids == list(range(1, len(ids) + 1))
    total_views = sum(len(s.views) for s in list_section_specs())
    assert len(VIEW_ID_MAP) == total_views
