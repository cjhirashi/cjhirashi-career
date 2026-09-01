"""Tool Bedrock ``admin_view_settings`` (reemplaza ``admin_section_settings``)."""
import pytest

from services.bedrock.tools import (
    _RAW_TOOLS,
    _WRITE_TOOLS,
    invalidation_key,
    _run_admin_view_settings,
    all_tool_names,
)
from services.bedrock.agent_profiles import _CONFIGURATION_TOOL_NAMES


def test_tool_registered_and_old_one_gone():
    assert "admin_view_settings" in all_tool_names()
    assert "admin_section_settings" not in all_tool_names()
    assert "admin_view_settings" in _WRITE_TOOLS
    assert "admin_section_settings" not in _WRITE_TOOLS
    assert "admin_view_settings" in _CONFIGURATION_TOOL_NAMES
    assert "admin_section_settings" not in _CONFIGURATION_TOOL_NAMES
    spec = next(t for t in _RAW_TOOLS if t["name"] == "admin_view_settings")
    assert spec["schema"]["properties"]["action"]["enum"] == ["list", "get", "update"]


def test_changelog_resource_key():
    assert (
        invalidation_key("admin_view_settings", {"action": "update"}, {}) == "admin-views"
    )
    assert invalidation_key("admin_view_settings", {"action": "list"}, {}) is None


async def test_list_and_get(hier_db):
    listed = await _run_admin_view_settings(hier_db, {"action": "list"})
    assert listed["items"] and all("owner" in it for it in listed["items"])
    scoped = await _run_admin_view_settings(
        hier_db, {"action": "list", "section_id": "s1-39"}
    )
    assert {it["key"] for it in scoped["items"]} == {"list", "view", "edit"}
    bad = await _run_admin_view_settings(
        hier_db, {"action": "list", "section_id": "s9-9"}
    )
    assert "error" in bad and "s1-N" in bad["error"]

    vid = scoped["items"][0]["id"]
    got = await _run_admin_view_settings(hier_db, {"action": "get", "view_id": vid})
    assert got["item"]["id"] == vid


async def test_get_requires_view_id_and_reports_unknown(hier_db):
    assert "error" in await _run_admin_view_settings(hier_db, {"action": "get"})
    unknown = await _run_admin_view_settings(
        hier_db, {"action": "get", "view_id": "vw-99999"}
    )
    assert "unknown admin view" in unknown["error"]


async def test_update_sets_responsible_and_instructions(hier_db):
    listed = await _run_admin_view_settings(
        hier_db, {"action": "list", "section_id": "s1-39"}
    )
    vid = next(it["id"] for it in listed["items"] if it["key"] == "list")

    ok = await _run_admin_view_settings(
        hier_db,
        {
            "action": "update",
            "view_id": vid,
            "responsible_agent_profile_id": "agent_search_operations",
            "instructions": "Cuida el embudo.",
        },
    )
    assert ok["item"]["responsible_agent_profile_id"] == "agent_search_operations"
    assert ok["item"]["instructions"] == "Cuida el embudo."

    cleared = await _run_admin_view_settings(
        hier_db,
        {"action": "update", "view_id": vid, "responsible_agent_profile_id": ""},
    )
    assert cleared["item"]["responsible_agent_profile_id"] is None


async def test_update_rejects_l3_with_l2_hint(hier_db):
    listed = await _run_admin_view_settings(
        hier_db, {"action": "list", "section_id": "s1-39"}
    )
    vid = listed["items"][0]["id"]
    res = await _run_admin_view_settings(
        hier_db,
        {
            "action": "update",
            "view_id": vid,
            "responsible_agent_profile_id": "agent_vacancy_search",
        },
    )
    assert "error" in res and "L2" in res["error"]

    res2 = await _run_admin_view_settings(
        hier_db,
        {"action": "update", "view_id": vid, "responsible_agent_profile_id": "agent_nope"},
    )
    assert "unknown agent profile" in res2["error"]


async def test_update_without_fields_errors(hier_db):
    listed = await _run_admin_view_settings(
        hier_db, {"action": "list", "section_id": "s1-39"}
    )
    res = await _run_admin_view_settings(
        hier_db, {"action": "update", "view_id": listed["items"][0]["id"]}
    )
    assert "requiere responsible_agent_profile_id" in res["error"]


async def test_unknown_action(hier_db):
    res = await _run_admin_view_settings(
        hier_db, {"action": "frobnicate", "view_id": "vw-1"}
    )
    assert res["error"].startswith("unknown action")
