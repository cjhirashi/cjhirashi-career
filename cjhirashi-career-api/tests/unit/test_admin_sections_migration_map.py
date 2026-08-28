"""Anti-drift de los mapas CONGELADOS de la migración ADR-022 (c4d5e6f7a8b9).

El snapshot embebido en la migración (que NO importa ``services.admin_sections``)
debe seguir cuadrando 1:1 con el registro de código vivo y con el seeder
idempotente.
"""
import importlib.util
from pathlib import Path

from services.admin_sections import GROUPS, list_section_specs
from services.admin_sections_seed import VIEW_ID_MAP
from services.bedrock.agent_profiles import get_profile

_VERSIONS = Path(__file__).resolve().parents[2] / "alembic" / "versions"
_MIG_ADR021 = _VERSIONS / "b2c3d4e5f6a7_admin_section_overrides_synthetic_pk.py"
_MIG_ADR022 = _VERSIONS / "c4d5e6f7a8b9_admin_sections_hierarchy_views.py"


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_MIG = _load(_MIG_ADR022)


def test_sec_to_s1_is_identity_on_the_integer():
    assert _MIG._SEC_TO_S1 == {f"sec-{n}": f"s1-{n}" for n in range(1, 55)}
    live_ids = {spec.id for spec in list_section_specs()}
    assert set(_MIG._SEC_TO_S1.values()) == live_ids


def test_sec_to_s1_matches_adr021_frozen_map():
    slug_to_pk = _load(_MIG_ADR021)._SLUG_TO_PK  # slug -> sec-N
    code = {spec.system_name: spec.id for spec in list_section_specs()}  # slug -> s1-N
    assert set(slug_to_pk) == set(code)
    for slug, sec_id in slug_to_pk.items():
        n = sec_id.split("-")[1]
        assert code[slug] == f"s1-{n}"


def test_frozen_groups_match_code_registry():
    assert _MIG._FROZEN_GROUPS == [list(g) for g in GROUPS] or _MIG._FROZEN_GROUPS == [
        tuple(g) for g in GROUPS
    ]
    live_names = {name for _gid, _sys, name, _so in GROUPS}
    used = {spec.group for spec in list_section_specs()}
    assert used <= live_names


def test_profile_levels_snapshot_matches_live_catalog():
    for pid, level in _MIG._PROFILE_LEVELS.items():
        assert get_profile(pid).level == level


def test_l3_chat_fallback_targets_are_l2_or_l1():
    for src, dst in _MIG._L3_CHAT_FALLBACK.items():
        assert _MIG._PROFILE_LEVELS[src] == 3
        assert _MIG._PROFILE_LEVELS[dst] in (1, 2)


def test_embedded_section_snapshot_matches_registry():
    live = {
        int(s.id.split("-")[1]): (
            s.system_name,
            s.label,
            s.path,
            s.section_type,
            s.group,
            s.sort_order,
            s.singleton,
            s.default_agent_profile_id or None,
            tuple(s.related_tools),
        )
        for s in list_section_specs()
    }
    snap = {
        row[0]: (row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8] or None, tuple(row[9]))
        for row in _MIG._SECTIONS
    }
    assert snap == live


def test_migration_plan_equals_live_seeder_structure():
    groups, l1_rows, views, principal_by_s1 = _MIG._plan()

    assert [(g["id"], g["system_name"], g["name"], g["sort_order"]) for g in groups] == [
        tuple(g) for g in GROUPS
    ]

    live_pairs = {
        (spec.id, view.key) for spec in list_section_specs() for view in spec.views
    }
    assert {(v["owner_l1_id"], v["key"]) for v in views} == live_pairs
    assert {v["id"] for v in views} == set(VIEW_ID_MAP.values())

    live_meta = {
        (spec.id, view.key): (view.data_source, view.resource_key, tuple(view.tool_names))
        for spec in list_section_specs()
        for view in spec.views
    }
    for v in views:
        assert live_meta[(v["owner_l1_id"], v["key"])] == (
            v["data_source"],
            v["resource_key"],
            tuple(v["tool_names"]),
        )


def test_principal_responsible_is_l2_or_none():
    _g, _l1, views, _p = _MIG._plan()
    for v in views:
        rid = v["responsible_agent_profile_id"]
        if rid is not None:
            assert _MIG._PROFILE_LEVELS[rid] == 2
            assert v["sort_order"] == 0  # solo la vista principal


def test_override_conversion_helpers():
    # agente L2 → se conserva; L3 → None; L1 → None
    assert _MIG._responsible("agent_search_operations") == "agent_search_operations"
    assert _MIG._responsible("agent_vacancy_search") == "agent_search_operations"  # fallback L2
    assert _MIG._responsible("agent_task_manager") is None  # fallback es L1
    assert _MIG._responsible("agent_orchestrator") is None
    assert _MIG._responsible(None) is None
