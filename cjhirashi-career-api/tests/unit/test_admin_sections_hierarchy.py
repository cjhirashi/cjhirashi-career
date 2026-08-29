"""Catálogo runtime, endpoints y resolución de perfil de la jerarquía ADR-022.

SQLite in-memory (fixture ``hier_db``), llamando a los handlers de ruta y a
``section_catalog`` directamente.
"""
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from models.admin_view import AdminView
from routes import admin_sections as routes
from schemas.admin_sections import (
    AdminViewUpdateRequest,
    GroupOrderRequest,
    SectionGroupUpdateRequest,
    SectionReorderRequest,
    SectionUpdateRequest,
)
from services import section_catalog
from services.bedrock.agent_profiles import AGENT_ORCHESTRATOR

_USER = MagicMock()
_USER.is_superuser = True  # superusuario — ve todos los grupos incluyendo admin

_STANDARD_USER = MagicMock()
_STANDARD_USER.is_superuser = False  # usuario estándar — no ve el grupo admin


# ---------------------------------------------------------------------------
# nav-tree
# ---------------------------------------------------------------------------


async def test_nav_tree_shape(hier_db):
    # Usuario estándar no ve el grupo admin (visibility_level='superuser')
    tree = await routes.get_nav_tree(current_user=_STANDARD_USER, db=hier_db)
    assert set(tree) == {"groups", "generated_at"}
    assert len(tree["groups"]) == 11
    # grupos ordenados por sort_order
    orders = [g["sort_order"] for g in tree["groups"]]
    assert orders == sorted(orders)
    metrics = next(g for g in tree["groups"] if g["system_name"] == "metrics")
    dash = next(s for s in metrics["sections"] if s["system_name"] == "dashboard")
    assert dash["level"] == 1
    assert dash["has_layout"] is True
    assert dash["view_count"] == 1
    assert dash["children"] == []
    v = dash["views"][0]
    assert v["data_source"] == "computed"
    assert v["chat_enabled"] is False
    assert v["has_instructions"] is False
    assert "instructions" not in v  # el texto completo NO va en el árbol


async def test_nav_tree_is_cached_until_invalidated(hier_db):
    await routes.get_nav_tree(current_user=_USER, db=hier_db)
    assert section_catalog._CACHE is not None
    section_catalog.invalidate_cache()
    assert section_catalog._CACHE is None


# ---------------------------------------------------------------------------
# Grupos
# ---------------------------------------------------------------------------


async def test_reorder_groups_assigns_multiples_of_ten(hier_db):
    groups = await routes.list_section_groups(current_user=_USER, db=hier_db)
    ids = [g["id"] for g in groups][::-1]
    out = await routes.reorder_section_groups(
        GroupOrderRequest(order=ids), current_user=_USER, db=hier_db
    )
    assert [g["id"] for g in out] == ids
    assert [g["sort_order"] for g in out] == [i * 10 for i in range(len(ids))]


async def test_reorder_groups_rejects_incomplete_list(hier_db):
    with pytest.raises(Exception) as exc:
        await routes.reorder_section_groups(
            GroupOrderRequest(order=["grp-1"]), current_user=_USER, db=hier_db
        )
    assert exc.value.status_code == 400


async def test_update_single_group(hier_db):
    out = await routes.update_section_group(
        "grp-1", SectionGroupUpdateRequest(sort_order=7), current_user=_USER, db=hier_db
    )
    assert out["sort_order"] == 7
    with pytest.raises(Exception) as exc:
        await routes.update_section_group(
            "grp-999", SectionGroupUpdateRequest(sort_order=1), current_user=_USER, db=hier_db
        )
    assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# Secciones
# ---------------------------------------------------------------------------


async def test_list_sections_by_level(hier_db):
    l1 = await routes.list_or_get_section("l1", current_user=_USER, db=hier_db)
    assert len(l1) == 54
    assert await routes.list_or_get_section("l2", current_user=_USER, db=hier_db) == []
    assert await routes.list_or_get_section("l3", current_user=_USER, db=hier_db) == []


async def test_get_section_detail_and_404(hier_db):
    detail = await routes.list_or_get_section("s1-39", current_user=_USER, db=hier_db)
    assert detail["system_name"] == "career-vacancies"
    assert [v["key"] for v in detail["views"]] == ["list", "view", "edit"]
    with pytest.raises(Exception) as exc:
        await routes.list_or_get_section("s1-9999", current_user=_USER, db=hier_db)
    assert exc.value.status_code == 404


async def test_update_section_move_l1_to_other_group(hier_db):
    out = await routes.update_section(
        "s1-1",
        SectionUpdateRequest(group_id="grp-8", sort_order=5),
        current_user=_USER,
        db=hier_db,
    )
    assert out["group_id"] == "grp-8"
    assert out["sort_order"] == 5


async def test_update_section_rejects_parent_id_on_l1(hier_db):
    with pytest.raises(Exception) as exc:
        await routes.update_section(
            "s1-1",
            SectionUpdateRequest(parent_id="s1-2"),
            current_user=_USER,
            db=hier_db,
        )
    assert exc.value.status_code == 400


async def test_update_section_unknown_group_is_400(hier_db):
    with pytest.raises(Exception) as exc:
        await routes.update_section(
            "s1-1",
            SectionUpdateRequest(group_id="grp-nope"),
            current_user=_USER,
            db=hier_db,
        )
    assert exc.value.status_code == 400


async def test_reorder_sections_within_group(hier_db):
    l1 = await section_catalog.list_sections(hier_db, 1)
    in_metrics = [s["id"] for s in l1 if s["group_id"] == "grp-1"]
    reordered = in_metrics[::-1]
    out = await routes.reorder_sections(
        SectionReorderRequest(container_id="grp-1", order=reordered),
        current_user=_USER,
        db=hier_db,
    )
    by_id = {s["id"]: s for s in out}
    assert [by_id[i]["sort_order"] for i in reordered] == [i * 10 for i in range(len(reordered))]


# ---------------------------------------------------------------------------
# Vistas
# ---------------------------------------------------------------------------


async def test_list_views_and_filters(hier_db):
    all_views = await routes.list_views(current_user=_USER, db=hier_db)
    assert len(all_views) == 123
    one = await routes.list_views(section_id="s1-39", current_user=_USER, db=hier_db)
    assert {v["key"] for v in one} == {"list", "view", "edit"}
    crud = await routes.list_views(data_source="computed", current_user=_USER, db=hier_db)
    assert crud and all(v["data_source"] == "computed" for v in crud)
    with pytest.raises(Exception) as exc:
        await routes.list_views(section_id="s9-9", current_user=_USER, db=hier_db)
    assert exc.value.status_code == 400


async def test_update_view_sets_and_clears_responsible(hier_db):
    views = await routes.list_views(section_id="s1-39", current_user=_USER, db=hier_db)
    vid = next(v["id"] for v in views if v["key"] == "list")

    updated = await routes.update_view(
        vid,
        AdminViewUpdateRequest(responsible_agent_profile_id="agent_search_operations"),
        current_user=_USER,
        db=hier_db,
    )
    assert updated["responsible_agent_profile_id"] == "agent_search_operations"
    assert updated["responsible_is_l2"] is True
    assert updated["chat_enabled"] is True

    cleared = await routes.update_view(
        vid,
        AdminViewUpdateRequest(responsible_agent_profile_id=""),
        current_user=_USER,
        db=hier_db,
    )
    assert cleared["responsible_agent_profile_id"] is None
    assert cleared["chat_enabled"] is False


async def test_update_view_rejects_non_l2(hier_db):
    views = await routes.list_views(section_id="s1-39", current_user=_USER, db=hier_db)
    vid = views[0]["id"]
    with pytest.raises(Exception) as exc:
        await routes.update_view(
            vid,
            AdminViewUpdateRequest(responsible_agent_profile_id="agent_vacancy_search"),  # L3
            current_user=_USER,
            db=hier_db,
        )
    assert exc.value.status_code == 400
    assert "L2" in exc.value.detail


async def test_update_view_unknown_profile_and_view(hier_db):
    views = await routes.list_views(section_id="s1-39", current_user=_USER, db=hier_db)
    with pytest.raises(Exception) as exc:
        await routes.update_view(
            views[0]["id"],
            AdminViewUpdateRequest(responsible_agent_profile_id="agent_nope"),
            current_user=_USER,
            db=hier_db,
        )
    assert exc.value.status_code == 400 and "unknown agent profile" in exc.value.detail
    with pytest.raises(Exception) as exc:
        await routes.get_view("vw-99999", current_user=_USER, db=hier_db)
    assert exc.value.status_code == 404


async def test_update_view_extra_field_forbidden():
    with pytest.raises(Exception):
        AdminViewUpdateRequest(tool_names=["x"])  # extra="forbid"


async def test_update_view_empty_body_is_400(hier_db):
    views = await routes.list_views(section_id="s1-39", current_user=_USER, db=hier_db)
    with pytest.raises(Exception) as exc:
        await routes.update_view(
            views[0]["id"], AdminViewUpdateRequest(), current_user=_USER, db=hier_db
        )
    assert exc.value.status_code == 400


async def test_update_view_instructions_whitespace_clears(hier_db):
    views = await routes.list_views(section_id="s1-39", current_user=_USER, db=hier_db)
    vid = views[0]["id"]
    await routes.update_view(
        vid, AdminViewUpdateRequest(instructions="  hola  "), current_user=_USER, db=hier_db
    )
    got = await routes.get_view(vid, current_user=_USER, db=hier_db)
    assert got["instructions"] == "hola"
    await routes.update_view(
        vid, AdminViewUpdateRequest(instructions="   "), current_user=_USER, db=hier_db
    )
    got = await routes.get_view(vid, current_user=_USER, db=hier_db)
    assert got["instructions"] is None
    assert got["instructions_enabled"] is False


# ---------------------------------------------------------------------------
# CHECK single-owner + índices únicos parciales
# ---------------------------------------------------------------------------


async def test_single_owner_check_rejects_zero_and_two_owners(hier_db_empty):
    hier_db_empty.add(AdminView(id="vw-x", key="k", label="l", data_source="crud"))
    with pytest.raises(IntegrityError):
        await hier_db_empty.flush()
    await hier_db_empty.rollback()

    hier_db_empty.add(
        AdminView(id="vw-y", owner_l1_id="s1-1", owner_l2_id="s2-1", key="k", label="l", data_source="crud")
    )
    with pytest.raises(IntegrityError):
        await hier_db_empty.flush()
    await hier_db_empty.rollback()


async def test_resource_key_scope_check(hier_db_empty):
    hier_db_empty.add(
        AdminView(
            id="vw-z",
            owner_l1_id="s1-1",
            key="k",
            label="l",
            data_source="computed",
            resource_key="vacancies",
        )
    )
    with pytest.raises(IntegrityError):
        await hier_db_empty.flush()


async def test_partial_unique_key_per_section(hier_db):
    hier_db.add(
        AdminView(id="vw-dup", owner_l1_id="s1-39", key="list", label="dup", data_source="crud")
    )
    with pytest.raises(IntegrityError):
        await hier_db.flush()


# ---------------------------------------------------------------------------
# match_active_view / resolve_profile_for_turn
# ---------------------------------------------------------------------------


async def test_match_active_view_exact_prefix_and_view_key(hier_db):
    exact = await section_catalog.match_active_view(hier_db, "/career/vacancies")
    assert exact.section_id == "s1-39" and exact.view_key == "list"

    detail = await section_catalog.match_active_view(hier_db, "/career/vacancies/vac-1")
    assert detail.view_key == "view"

    forced = await section_catalog.match_active_view(
        hier_db, "/career/vacancies/vac-1", view_key="edit"
    )
    assert forced.view_key == "edit"

    assert await section_catalog.match_active_view(hier_db, "/nope") is None


async def test_resolve_profile_for_turn_paths(hier_db):
    # general → orquestador
    prof = await section_catalog.resolve_profile_for_turn(
        hier_db, chat_surface="general", agent_profile_id=None, page_context=None
    )
    assert prof.id == AGENT_ORCHESTRATOR

    # override explícito gana
    prof = await section_catalog.resolve_profile_for_turn(
        hier_db,
        chat_surface="contextual",
        agent_profile_id="agent_networking",
        page_context={"route": "/career/vacancies"},
    )
    assert prof.id == "agent_networking"

    # sin responsable en la vista → orquestador
    prof = await section_catalog.resolve_profile_for_turn(
        hier_db,
        chat_surface="contextual",
        agent_profile_id=None,
        page_context={"route": "/career/vacancies"},
    )
    assert prof.id == AGENT_ORCHESTRATOR

    # con responsable L2 en la vista activa → ese
    await section_catalog.update_view(
        hier_db,
        (await section_catalog.match_active_view(hier_db, "/career/vacancies")).view_id,
        responsible="agent_search_operations",
    )
    prof = await section_catalog.resolve_profile_for_turn(
        hier_db,
        chat_surface="contextual",
        agent_profile_id=None,
        page_context={"route": "/career/vacancies"},
    )
    assert prof.id == "agent_search_operations"
