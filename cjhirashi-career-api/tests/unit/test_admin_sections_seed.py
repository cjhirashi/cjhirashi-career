"""Seeder de arranque de la jerarquía de secciones del Admin (ADR-022; ADR-023 corrección).

Desde la corrección, ``ensure_admin_group_and_section`` (alta idempotente,
NUNCA UPDATE) reemplaza el upsert/prune de grupos y secciones L1; ``sync_views``
(recortada) sigue upsert + prune de vistas, pero ya no crea la sección dueña si
falta — la fixture ``hier_db`` compone ambas para dejar el estado equivalente al
seed histórico (11 grupos + 1 `admin`, 54 secciones + 1 `admin-sections`, 123
vistas de código).
"""
import pytest
from sqlalchemy import func, select

from models.admin_section_group import AdminSectionGroup
from models.admin_section_l1 import AdminSectionL1
from models.admin_view import AdminView
from services.admin_sections import GROUPS, list_section_specs
from services.admin_sections_seed import (
    ADMIN_GROUP_ID,
    ADMIN_GROUP_SYSTEM_NAME,
    ADMIN_SECTION_ID,
    ADMIN_SECTION_SYSTEM_NAME,
    VIEW_ID_MAP,
    _L3_CHAT_FALLBACK,
    ensure_admin_group_and_section,
    sync_views,
)
from services.bedrock.agent_profiles import get_profile


async def _count(session, model):
    return (await session.execute(select(func.count()).select_from(model))).scalar()


async def _seed_legacy(session) -> None:
    """Replica conftest._seed_legacy_groups_and_sections para tests que usan hier_session_factory."""
    for gid, system_name, name, sort_order in GROUPS:
        session.add(AdminSectionGroup(id=gid, system_name=system_name, name=name, sort_order=sort_order, origin="code"))
    await session.flush()
    group_id_by_name = {name: gid for gid, _sys, name, _so in GROUPS}
    for spec in list_section_specs():
        session.add(AdminSectionL1(id=spec.id, group_id=group_id_by_name[spec.group], system_name=spec.system_name, label=spec.label, path=spec.path, section_type=spec.section_type, sort_order=spec.sort_order, origin="code"))
    await session.flush()


async def _seed_full(session) -> None:
    await _seed_legacy(session)
    await ensure_admin_group_and_section(session)
    await sync_views(session)


async def test_seed_creates_full_structure(hier_db):
    # hier_db ya está poblada por conftest._seed_full.
    # 11 + 1 (admin) grupos; s1-17 se migra a admin-sections (UPDATE, no INSERT)
    # → total L1 sigue siendo 54, no 55. 123 vistas de código.
    assert await _count(hier_db, AdminSectionGroup) == 12
    assert await _count(hier_db, AdminSectionL1) == 54
    assert await _count(hier_db, AdminView) == len(VIEW_ID_MAP) == 123


async def test_seed_never_writes_operator_columns(hier_db):
    rows = (await hier_db.execute(select(AdminView))).scalars().all()
    assert all(r.responsible_agent_profile_id is None for r in rows)
    assert all(r.instructions is None for r in rows)
    assert all(r.origin == "code" for r in rows)


async def test_ensure_admin_group_and_section_is_idempotent(hier_session_factory):
    async with hier_session_factory() as s:
        await ensure_admin_group_and_section(s)
        await s.commit()
    async with hier_session_factory() as s:
        await ensure_admin_group_and_section(s)
        await s.commit()
    async with hier_session_factory() as s:
        groups = (
            await s.execute(
                select(AdminSectionGroup).where(
                    AdminSectionGroup.system_name == ADMIN_GROUP_SYSTEM_NAME
                )
            )
        ).scalars().all()
        assert len(groups) == 1
        assert groups[0].id == ADMIN_GROUP_ID
        sections = (
            await s.execute(
                select(AdminSectionL1).where(
                    AdminSectionL1.system_name == ADMIN_SECTION_SYSTEM_NAME
                )
            )
        ).scalars().all()
        assert len(sections) == 1
        assert sections[0].id == ADMIN_SECTION_ID


async def test_ensure_admin_group_and_section_never_updates_existing(hier_session_factory):
    async with hier_session_factory() as s:
        await ensure_admin_group_and_section(s)
        await s.commit()
    async with hier_session_factory() as s:
        grp = (
            await s.execute(
                select(AdminSectionGroup).where(
                    AdminSectionGroup.system_name == ADMIN_GROUP_SYSTEM_NAME
                )
            )
        ).scalar_one()
        grp.name = "Renombrado por el operador"
        sec = (
            await s.execute(
                select(AdminSectionL1).where(
                    AdminSectionL1.system_name == ADMIN_SECTION_SYSTEM_NAME
                )
            )
        ).scalar_one()
        sec.label = "También renombrada"
        await s.commit()
    async with hier_session_factory() as s:
        await ensure_admin_group_and_section(s)
        await s.commit()
    async with hier_session_factory() as s:
        grp = (
            await s.execute(
                select(AdminSectionGroup).where(
                    AdminSectionGroup.system_name == ADMIN_GROUP_SYSTEM_NAME
                )
            )
        ).scalar_one()
        assert grp.name == "Renombrado por el operador"
        sec = (
            await s.execute(
                select(AdminSectionL1).where(
                    AdminSectionL1.system_name == ADMIN_SECTION_SYSTEM_NAME
                )
            )
        ).scalar_one()
        assert sec.label == "También renombrada"


async def test_sync_views_is_idempotent(hier_session_factory):
    async with hier_session_factory() as s:
        await _seed_full(s)
        await s.commit()
    # Segunda pasada: solo las partes idempotentes (sin re-insertar el seed legacy)
    async with hier_session_factory() as s:
        await ensure_admin_group_and_section(s)
        await sync_views(s)
        await s.commit()
    async with hier_session_factory() as s:
        assert await _count(s, AdminView) == 123
        assert await _count(s, AdminSectionL1) == 54


async def test_sync_views_preserves_operator_sort_order_and_group(hier_session_factory):
    async with hier_session_factory() as s:
        await _seed_full(s)
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
        await sync_views(s)
        await s.commit()
    async with hier_session_factory() as s:
        row = (
            await s.execute(select(AdminSectionL1).where(AdminSectionL1.system_name == "dashboard"))
        ).scalar_one()
        assert row.sort_order == 999  # sync_views no toca secciones, solo vistas
        grp = (
            await s.execute(
                select(AdminSectionGroup).where(AdminSectionGroup.system_name == "settings")
            )
        ).scalar_one()
        assert row.group_id == grp.id


async def test_sync_views_prunes_orphan_code_rows(hier_session_factory):
    async with hier_session_factory() as s:
        await _seed_full(s)
        await s.commit()
    async with hier_session_factory() as s:
        l1 = (
            await s.execute(
                select(AdminSectionL1).where(AdminSectionL1.system_name == "dashboard")
            )
        ).scalar_one()
        s.add(
            AdminView(
                id="vw-9000",
                owner_l1_id=l1.id,
                key="ghost",
                label="Ghost",
                sort_order=99,
                data_source="crud",
                resource_key=None,
                origin="code",
            )
        )
        await s.commit()
    async with hier_session_factory() as s:
        await sync_views(s)
        await s.commit()
    async with hier_session_factory() as s:
        assert (
            await s.execute(select(AdminView).where(AdminView.id == "vw-9000"))
        ).scalar_one_or_none() is None


async def test_sync_views_does_not_prune_admin_owned_rows(hier_session_factory):
    async with hier_session_factory() as s:
        await _seed_full(s)
        await s.commit()
    async with hier_session_factory() as s:
        l1 = (
            await s.execute(
                select(AdminSectionL1).where(AdminSectionL1.system_name == "dashboard")
            )
        ).scalar_one()
        s.add(
            AdminView(
                id="vw-8000",
                owner_l1_id=l1.id,
                key="operator-view",
                label="Operador",
                sort_order=50,
                data_source="crud",
                resource_key=None,
                origin="admin",
            )
        )
        await s.commit()
    async with hier_session_factory() as s:
        await sync_views(s)
        await s.commit()
    async with hier_session_factory() as s:
        assert (
            await s.execute(select(AdminView).where(AdminView.id == "vw-8000"))
        ).scalar_one_or_none() is not None


async def test_sync_views_skips_section_deleted_by_operator(hier_session_factory, caplog):
    async with hier_session_factory() as s:
        await _seed_full(s)
        await s.commit()
    async with hier_session_factory() as s:
        l1 = (
            await s.execute(
                select(AdminSectionL1).where(AdminSectionL1.system_name == "dashboard")
            )
        ).scalar_one()
        await s.delete(l1)
        await s.commit()
    async with hier_session_factory() as s:
        import logging

        with caplog.at_level(logging.WARNING):
            await sync_views(s)
        await s.commit()
        assert any("dashboard" in rec.message for rec in caplog.records)


def test_l3_chat_fallback_resolves_to_l2_or_nothing():
    for source, target in _L3_CHAT_FALLBACK.items():
        assert get_profile(source).level == 3
        assert get_profile(target).level in (1, 2)


def test_view_id_map_is_contiguous_and_covers_registry():
    ids = sorted(int(v.split("-")[1]) for v in VIEW_ID_MAP.values())
    assert ids == list(range(1, len(ids) + 1))
    total_views = sum(len(s.views) for s in list_section_specs())
    assert len(VIEW_ID_MAP) == total_views
