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


# ---------------------------------------------------------------------------
# create_group
# ---------------------------------------------------------------------------


async def test_create_group_ok_returns_201(hier_db_bare):
    from schemas.admin_sections import SectionGroupCreateRequest

    result = await routes.create_section_group(
        SectionGroupCreateRequest(name="Nuevo Grupo", system_name="nuevo-grupo"),
        current_user=_USER,
        db=hier_db_bare,
    )
    assert result["system_name"] == "nuevo-grupo"
    assert result["name"] == "Nuevo Grupo"
    assert result["visibility_level"] == "standard"


async def test_create_group_auto_sort_order(hier_db_bare):
    from schemas.admin_sections import SectionGroupCreateRequest

    result = await routes.create_section_group(
        SectionGroupCreateRequest(name="Auto Sort", system_name="auto-sort"),
        current_user=_USER,
        db=hier_db_bare,
    )
    # sort_order auto asignado (max existente + 10, o 10 si no hay nada)
    assert isinstance(result["sort_order"], int)
    assert result["sort_order"] > 0


async def test_create_group_explicit_sort_order(hier_db_bare):
    from schemas.admin_sections import SectionGroupCreateRequest

    result = await routes.create_section_group(
        SectionGroupCreateRequest(name="Grupo 99", system_name="grupo-99", sort_order=99),
        current_user=_USER,
        db=hier_db_bare,
    )
    assert result["sort_order"] == 99


async def test_create_group_duplicate_name_is_409(hier_db_bare):
    from schemas.admin_sections import SectionGroupCreateRequest

    await routes.create_section_group(
        SectionGroupCreateRequest(name="Duplicado", system_name="duplicado-1"),
        current_user=_USER,
        db=hier_db_bare,
    )
    section_catalog.invalidate_cache()
    with pytest.raises(Exception) as exc:
        await routes.create_section_group(
            SectionGroupCreateRequest(name="Duplicado", system_name="duplicado-2"),
            current_user=_USER,
            db=hier_db_bare,
        )
    assert exc.value.status_code == 409


async def test_create_group_duplicate_system_name_is_409(hier_db_bare):
    from schemas.admin_sections import SectionGroupCreateRequest

    await routes.create_section_group(
        SectionGroupCreateRequest(name="Grupo A", system_name="mismo-sys"),
        current_user=_USER,
        db=hier_db_bare,
    )
    section_catalog.invalidate_cache()
    with pytest.raises(Exception) as exc:
        await routes.create_section_group(
            SectionGroupCreateRequest(name="Grupo B", system_name="mismo-sys"),
            current_user=_USER,
            db=hier_db_bare,
        )
    assert exc.value.status_code == 409


async def test_create_group_reserved_system_name_admin_is_400(hier_db_bare):
    from schemas.admin_sections import SectionGroupCreateRequest

    with pytest.raises(Exception) as exc:
        await routes.create_section_group(
            SectionGroupCreateRequest(name="Admin Reservado", system_name="admin"),
            current_user=_USER,
            db=hier_db_bare,
        )
    assert exc.value.status_code == 403


async def test_create_group_invalid_visibility_is_422():
    from pydantic import ValidationError
    from schemas.admin_sections import SectionGroupCreateRequest

    with pytest.raises(ValidationError):
        SectionGroupCreateRequest(name="X", system_name="x-group", visibility_level="invalid")


async def test_create_group_superuser_visibility(hier_db_bare):
    from schemas.admin_sections import SectionGroupCreateRequest

    result = await routes.create_section_group(
        SectionGroupCreateRequest(
            name="Solo Superuser", system_name="solo-superuser", visibility_level="superuser"
        ),
        current_user=_USER,
        db=hier_db_bare,
    )
    assert result["visibility_level"] == "superuser"


# ---------------------------------------------------------------------------
# delete_group
# ---------------------------------------------------------------------------


async def test_delete_group_empty_ok(hier_db_bare):
    from schemas.admin_sections import SectionGroupCreateRequest

    created = await routes.create_section_group(
        SectionGroupCreateRequest(name="Para Borrar", system_name="para-borrar"),
        current_user=_USER,
        db=hier_db_bare,
    )
    section_catalog.invalidate_cache()
    # No debe lanzar excepción (204 No Content)
    await routes.delete_section_group(created["id"], current_user=_USER, db=hier_db_bare)


async def test_delete_group_with_sections_is_409(hier_db):
    # hier_db tiene los 11 grupos legacy con secciones hijas
    # grp-1 = metrics, tiene secciones
    with pytest.raises(Exception) as exc:
        await routes.delete_section_group("grp-1", current_user=_USER, db=hier_db)
    assert exc.value.status_code == 409


async def test_delete_group_admin_is_403(hier_db_bare):
    # el grupo admin (grp-12) está protegido
    with pytest.raises(Exception) as exc:
        await routes.delete_section_group("grp-12", current_user=_USER, db=hier_db_bare)
    assert exc.value.status_code == 403


async def test_delete_group_not_found_is_404(hier_db_bare):
    with pytest.raises(Exception) as exc:
        await routes.delete_section_group("grp-9999", current_user=_USER, db=hier_db_bare)
    assert exc.value.status_code == 404


async def test_delete_group_superuser_visibility_blocked_for_standard(hier_db_bare):
    from schemas.admin_sections import SectionGroupCreateRequest

    # Crear grupo superuser
    created = await routes.create_section_group(
        SectionGroupCreateRequest(
            name="Solo Super", system_name="solo-super-del", visibility_level="superuser"
        ),
        current_user=_USER,
        db=hier_db_bare,
    )
    section_catalog.invalidate_cache()
    # Usuario estándar no puede borrarlo
    with pytest.raises(Exception) as exc:
        await routes.delete_section_group(created["id"], current_user=_STANDARD_USER, db=hier_db_bare)
    assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# create_section
# ---------------------------------------------------------------------------


async def test_create_section_l1_ok(hier_db_bare):
    from schemas.admin_sections import SectionCreateRequest

    # Primero crear un grupo no-admin para alojar la sección L1
    from schemas.admin_sections import SectionGroupCreateRequest
    grp = await routes.create_section_group(
        SectionGroupCreateRequest(name="Grupo Test L1", system_name="grp-test-l1"),
        current_user=_USER,
        db=hier_db_bare,
    )
    section_catalog.invalidate_cache()

    result = await routes.create_section(
        SectionCreateRequest(
            level=1,
            label="Mi Sección L1",
            system_name="mi-seccion-l1",
            section_type="table",
            group_id=grp["id"],
        ),
        current_user=_USER,
        db=hier_db_bare,
    )
    assert result["system_name"] == "mi-seccion-l1"
    assert result["level"] == 1
    assert result["group_id"] == grp["id"]
    assert result["origin"] == "admin"


async def test_create_section_l2_ok(hier_db):
    from schemas.admin_sections import SectionCreateRequest

    # Usar sección L1 existente (s1-1 = dashboard)
    result = await routes.create_section(
        SectionCreateRequest(
            level=2,
            label="Sub Sección L2",
            system_name="sub-seccion-l2",
            section_type="table",
            parent_id="s1-1",
        ),
        current_user=_USER,
        db=hier_db,
    )
    assert result["system_name"] == "sub-seccion-l2"
    assert result["level"] == 2
    assert result["parent_id"] == "s1-1"
    assert result["origin"] == "admin"


async def test_create_section_l3_ok(hier_db):
    from schemas.admin_sections import SectionCreateRequest

    # Primero crear una L2 como padre
    l2 = await routes.create_section(
        SectionCreateRequest(
            level=2,
            label="Padre L2",
            system_name="padre-l2-para-l3",
            section_type="table",
            parent_id="s1-1",
        ),
        current_user=_USER,
        db=hier_db,
    )
    section_catalog.invalidate_cache()

    result = await routes.create_section(
        SectionCreateRequest(
            level=3,
            label="Sub Sección L3",
            system_name="sub-seccion-l3",
            section_type="table",
            parent_id=l2["id"],
        ),
        current_user=_USER,
        db=hier_db,
    )
    assert result["system_name"] == "sub-seccion-l3"
    assert result["level"] == 3
    assert result["parent_id"] == l2["id"]


async def test_create_section_invalid_group_id_is_400(hier_db_bare):
    from schemas.admin_sections import SectionCreateRequest

    with pytest.raises(Exception) as exc:
        await routes.create_section(
            SectionCreateRequest(
                level=1,
                label="X",
                system_name="sec-bad-group",
                section_type="table",
                group_id="grp-9999",
            ),
            current_user=_USER,
            db=hier_db_bare,
        )
    assert exc.value.status_code == 400


async def test_create_section_duplicate_system_name_is_409(hier_db):
    from schemas.admin_sections import SectionCreateRequest

    await routes.create_section(
        SectionCreateRequest(
            level=2,
            label="Primero",
            system_name="dup-system-name",
            section_type="table",
            parent_id="s1-1",
        ),
        current_user=_USER,
        db=hier_db,
    )
    section_catalog.invalidate_cache()
    with pytest.raises(Exception) as exc:
        await routes.create_section(
            SectionCreateRequest(
                level=2,
                label="Segundo",
                system_name="dup-system-name",
                section_type="table",
                parent_id="s1-1",
            ),
            current_user=_USER,
            db=hier_db,
        )
    assert exc.value.status_code == 409


async def test_create_section_duplicate_path_is_409(hier_db):
    from schemas.admin_sections import SectionCreateRequest

    await routes.create_section(
        SectionCreateRequest(
            level=2,
            label="Con Path",
            system_name="con-path-1",
            section_type="table",
            path="/test/path-duplicado",
            parent_id="s1-1",
        ),
        current_user=_USER,
        db=hier_db,
    )
    section_catalog.invalidate_cache()
    with pytest.raises(Exception) as exc:
        await routes.create_section(
            SectionCreateRequest(
                level=2,
                label="Con Path Dup",
                system_name="con-path-2",
                section_type="table",
                path="/test/path-duplicado",
                parent_id="s1-1",
            ),
            current_user=_USER,
            db=hier_db,
        )
    assert exc.value.status_code == 409


async def test_create_section_invalid_visibility_is_422():
    from pydantic import ValidationError
    from schemas.admin_sections import SectionCreateRequest

    with pytest.raises(ValidationError):
        SectionCreateRequest(
            level=1,
            label="X",
            system_name="x-sec",
            section_type="table",
            group_id="grp-1",
            visibility_level="invalid-level",
        )


async def test_create_section_in_admin_group_is_403(hier_db_bare):
    from schemas.admin_sections import SectionCreateRequest

    # grp-12 = grupo admin (protegido)
    with pytest.raises(Exception) as exc:
        await routes.create_section(
            SectionCreateRequest(
                level=1,
                label="En Admin",
                system_name="en-admin-group",
                section_type="table",
                group_id="grp-12",
            ),
            current_user=_USER,
            db=hier_db_bare,
        )
    assert exc.value.status_code == 403


async def test_create_section_l2_invalid_parent_level_is_400(hier_db):
    """parent_id debe ser L1 para una sección L2."""
    from schemas.admin_sections import SectionCreateRequest

    # Crear primero una L2 para intentar usarla como padre de otra L2
    l2 = await routes.create_section(
        SectionCreateRequest(
            level=2,
            label="L2 para test",
            system_name="l2-for-bad-parent",
            section_type="table",
            parent_id="s1-1",
        ),
        current_user=_USER,
        db=hier_db,
    )
    section_catalog.invalidate_cache()

    with pytest.raises(Exception) as exc:
        await routes.create_section(
            SectionCreateRequest(
                level=2,
                label="L2 con padre incorrecto",
                system_name="l2-bad-parent",
                section_type="table",
                parent_id=l2["id"],  # L2 no puede ser padre de otra L2
            ),
            current_user=_USER,
            db=hier_db,
        )
    assert exc.value.status_code == 400


# ---------------------------------------------------------------------------
# delete_section
# ---------------------------------------------------------------------------


async def test_delete_section_without_children_or_views(hier_db_bare):
    from schemas.admin_sections import SectionCreateRequest, SectionGroupCreateRequest

    grp = await routes.create_section_group(
        SectionGroupCreateRequest(name="Grupo Para Sec", system_name="grp-para-sec"),
        current_user=_USER,
        db=hier_db_bare,
    )
    section_catalog.invalidate_cache()
    sec = await routes.create_section(
        SectionCreateRequest(
            level=1,
            label="Sec A Borrar",
            system_name="sec-a-borrar",
            section_type="table",
            group_id=grp["id"],
        ),
        current_user=_USER,
        db=hier_db_bare,
    )
    section_catalog.invalidate_cache()
    # No debe lanzar excepción (204 No Content)
    await routes.delete_section(sec["id"], current_user=_USER, db=hier_db_bare)


async def test_delete_section_with_children_is_409(hier_db):
    from schemas.admin_sections import SectionCreateRequest

    # Crear L1 con una L2 hija
    l1 = await routes.create_section(
        SectionCreateRequest(
            level=1,
            label="Padre con hijos",
            system_name="padre-con-hijos",
            section_type="table",
            group_id="grp-8",
        ),
        current_user=_USER,
        db=hier_db,
    )
    section_catalog.invalidate_cache()
    await routes.create_section(
        SectionCreateRequest(
            level=2,
            label="Hijo L2",
            system_name="hijo-l2-del-padre",
            section_type="table",
            parent_id=l1["id"],
        ),
        current_user=_USER,
        db=hier_db,
    )
    section_catalog.invalidate_cache()
    with pytest.raises(Exception) as exc:
        await routes.delete_section(l1["id"], current_user=_USER, db=hier_db)
    assert exc.value.status_code == 409


async def test_delete_section_admin_sections_is_403(hier_db_bare):
    # s1-55 = "admin-sections" — protegida, no puede borrarse
    with pytest.raises(Exception) as exc:
        await routes.delete_section("s1-55", current_user=_USER, db=hier_db_bare)
    assert exc.value.status_code == 403


async def test_delete_section_not_found_is_404(hier_db_bare):
    with pytest.raises(Exception) as exc:
        await routes.delete_section("s1-9999", current_user=_USER, db=hier_db_bare)
    assert exc.value.status_code == 404


async def test_delete_section_with_views_is_409(hier_db):
    # s1-1 (dashboard) tiene vistas sembradas
    with pytest.raises(Exception) as exc:
        await routes.delete_section("s1-1", current_user=_USER, db=hier_db)
    assert exc.value.status_code == 409


# ---------------------------------------------------------------------------
# move_section
# ---------------------------------------------------------------------------


async def test_move_section_l1_to_l2_ok(hier_db):
    from schemas.admin_sections import SectionCreateRequest, SectionMoveRequest

    # Crear una L1 nueva sin hijos ni vistas
    l1 = await routes.create_section(
        SectionCreateRequest(
            level=1,
            label="Para mover a L2",
            system_name="para-mover-a-l2",
            section_type="table",
            group_id="grp-8",
        ),
        current_user=_USER,
        db=hier_db,
    )
    section_catalog.invalidate_cache()

    # Moverla como L2 hija de s1-1 (dashboard)
    result = await routes.move_section(
        l1["id"],
        SectionMoveRequest(target_level=2, target_parent_id="s1-1"),
        current_user=_USER,
        db=hier_db,
    )
    assert result["level"] == 2
    assert result["parent_id"] == "s1-1"
    assert result["previous_id"] == l1["id"]
    assert result["system_name"] == "para-mover-a-l2"


async def test_move_section_with_children_is_409(hier_db):
    from schemas.admin_sections import SectionCreateRequest, SectionMoveRequest

    # Crear L1 con hijo L2
    l1 = await routes.create_section(
        SectionCreateRequest(
            level=1,
            label="L1 con hijos para move",
            system_name="l1-con-hijos-move",
            section_type="table",
            group_id="grp-8",
        ),
        current_user=_USER,
        db=hier_db,
    )
    section_catalog.invalidate_cache()
    await routes.create_section(
        SectionCreateRequest(
            level=2,
            label="Hijo L2 move",
            system_name="hijo-l2-move",
            section_type="table",
            parent_id=l1["id"],
        ),
        current_user=_USER,
        db=hier_db,
    )
    section_catalog.invalidate_cache()
    with pytest.raises(Exception) as exc:
        await routes.move_section(
            l1["id"],
            SectionMoveRequest(target_level=2, target_parent_id="s1-1"),
            current_user=_USER,
            db=hier_db,
        )
    assert exc.value.status_code == 409


async def test_move_section_admin_sections_is_403(hier_db_bare):
    from schemas.admin_sections import SectionMoveRequest

    # s1-55 es la sección protegida "admin-sections"
    with pytest.raises(Exception) as exc:
        await routes.move_section(
            "s1-55",
            SectionMoveRequest(target_level=2, target_parent_id="s1-55"),
            current_user=_USER,
            db=hier_db_bare,
        )
    assert exc.value.status_code == 403


async def test_move_section_same_level_is_400(hier_db):
    from schemas.admin_sections import SectionMoveRequest

    with pytest.raises(Exception) as exc:
        await routes.move_section(
            "s1-1",
            SectionMoveRequest(target_level=1, target_parent_id="grp-2"),
            current_user=_USER,
            db=hier_db,
        )
    assert exc.value.status_code == 400


async def test_move_section_not_found_is_404(hier_db_bare):
    from schemas.admin_sections import SectionMoveRequest

    with pytest.raises(Exception) as exc:
        await routes.move_section(
            "s1-9999",
            SectionMoveRequest(target_level=2, target_parent_id="s1-55"),
            current_user=_USER,
            db=hier_db_bare,
        )
    assert exc.value.status_code == 404


async def test_move_section_standard_user_blocked_on_superuser_section(hier_db_bare):
    """Un usuario estándar no puede mover secciones del árbol admin."""
    from schemas.admin_sections import SectionMoveRequest

    # s1-55 pertenece al grupo admin (superuser), _STANDARD_USER no puede moverla
    with pytest.raises(Exception) as exc:
        await routes.move_section(
            "s1-55",
            SectionMoveRequest(target_level=2, target_parent_id="s1-55"),
            current_user=_STANDARD_USER,
            db=hier_db_bare,
        )
    assert exc.value.status_code in (403, 403)


async def test_move_section_transfers_views(hier_db):
    """Las vistas de la sección migran al nuevo ID tras el move."""
    from schemas.admin_sections import SectionCreateRequest, SectionMoveRequest

    # Crear L2 con una vista propia
    l2 = await routes.create_section(
        SectionCreateRequest(
            level=2,
            label="L2 con vista",
            system_name="l2-con-vista-move",
            section_type="table",
            parent_id="s1-1",
        ),
        current_user=_USER,
        db=hier_db,
    )
    section_catalog.invalidate_cache()
    # Añadir una vista a la L2 recién creada
    from models.admin_view import AdminView
    hier_db.add(
        AdminView(
            id="vw-test-move",
            owner_l2_id=l2["id"],
            key="list",
            label="Lista",
            data_source="crud",
        )
    )
    await hier_db.flush()
    await hier_db.commit()
    section_catalog.invalidate_cache()

    # Mover L2 → L3 bajo otro L2 padre
    # Primero crear un L2 destino
    l2_destino = await routes.create_section(
        SectionCreateRequest(
            level=2,
            label="Destino L2",
            system_name="destino-l2-parent",
            section_type="table",
            parent_id="s1-2",
        ),
        current_user=_USER,
        db=hier_db,
    )
    section_catalog.invalidate_cache()

    result = await routes.move_section(
        l2["id"],
        SectionMoveRequest(target_level=3, target_parent_id=l2_destino["id"]),
        current_user=_USER,
        db=hier_db,
    )
    assert result["level"] == 3
    assert result["previous_id"] == l2["id"]
    # Las vistas se reasignan; el nuevo ID no es el mismo
    new_id = result["id"]
    assert new_id != l2["id"]
    # Verificar que la vista ahora apunta al nuevo ID
    views = await routes.list_views(section_id=new_id, current_user=_USER, db=hier_db)
    assert any(v["key"] == "list" for v in views)
