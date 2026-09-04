"""Catálogo efectivo de secciones del Admin — feature 001.

Unit puro sobre ``section_catalog`` (``_serialize`` / ``_view_override`` /
``_row_is_empty``): sin DB, con filas ``AdminSectionOverride`` construidas a mano.
"""
import pytest

from models.admin_section_override import AdminSectionOverride
from services.admin_sections import get_section_spec, list_section_specs
from services.section_catalog import _row_is_empty, _serialize, _view_override

_SEC_MAIN = "sec-1"       # dashboard: 1 vista "main", default_agent_profile_id = None
_SEC_MULTI = "sec-16"     # settings-agents: default_agent_profile_id = agent_configuration (L2)

_REMOVED_KEYS = ("chat_agent_profile_id", "description", "description_is_default")


def _main_view(section_id: str):
    return get_section_spec(section_id).views[0]


@pytest.mark.requisito("RF-001")
@pytest.mark.requisito("RF-005")
@pytest.mark.requisito("RF-016")
def test_serialize_without_override_shape():
    for spec in list_section_specs():
        item = _serialize(spec, None)
        for k in _REMOVED_KEYS:
            assert k not in item, f"{spec.id}: {k} no debe aparecer"
        assert "sidebar_has_chat" in item and isinstance(item["sidebar_has_chat"], bool)
        assert "sidebar_has_instructions" in item and isinstance(
            item["sidebar_has_instructions"], bool
        )
        # RF-001: agente efectivo L2 o None
        pid = item["agent_profile_id"]
        assert pid is None or pid == spec.default_agent_profile_id
        assert item["sidebar_has_chat"] is (pid is not None)
        # RF-016: sin override, toda vista con texto en código lo conserva
        for v in item["views"]:
            assert v["sidebar_body"], f"{spec.id}/{v['key']}: sidebar_body vacío sin override"
            assert v["is_default"] is True


@pytest.mark.requisito("RF-006")
def test_view_override_text():
    view = _main_view(_SEC_MAIN)
    out = _view_override({view.key: {"sidebar_body": "# Hola\n\n- uno"}}, view)
    assert out["sidebar_body"] == "# Hola\n\n- uno"
    assert out["is_default"] is False

    spec = get_section_spec(_SEC_MAIN)
    row = AdminSectionOverride(
        section_id=_SEC_MAIN, agent_profile_id=None,
        views={view.key: {"sidebar_body": "# Hola"}},
    )
    item = _serialize(spec, row)
    assert item["sidebar_has_instructions"] is True
    assert item["views"][0]["sidebar_body"] == "# Hola"


@pytest.mark.requisito("RF-007")
def test_view_override_explicit_empty_hides_instructions():
    view = _main_view(_SEC_MAIN)
    out = _view_override({view.key: {"sidebar_body": ""}}, view)
    assert out["sidebar_body"] == ""
    assert out["is_default"] is False

    spec = get_section_spec(_SEC_MAIN)  # 1 sola vista
    row = AdminSectionOverride(
        section_id=_SEC_MAIN, agent_profile_id=None,
        views={view.key: {"sidebar_body": ""}},
    )
    item = _serialize(spec, row)
    assert item["sidebar_has_instructions"] is False


@pytest.mark.requisito("RF-007b")
def test_view_override_missing_key_inherits():
    view = _main_view(_SEC_MAIN)
    out = _view_override({view.key: {"sidebar_title": "Título propio"}}, view)
    assert out["sidebar_title"] == "Título propio"
    assert out["sidebar_body"] == view.sidebar_body  # heredado de código
    assert out["is_default"] is False


def test_view_override_equal_to_code_is_default():
    view = _main_view(_SEC_MAIN)
    out = _view_override(
        {view.key: {"sidebar_title": view.sidebar_title, "sidebar_body": view.sidebar_body}},
        view,
    )
    assert out["is_default"] is True


@pytest.mark.requisito("RF-001")
def test_serialize_agent_override_label():
    spec = get_section_spec(_SEC_MAIN)
    row = AdminSectionOverride(
        section_id=_SEC_MAIN, agent_profile_id="agent_configuration", views=None
    )
    item = _serialize(spec, row)
    assert item["agent_profile_id"] == "agent_configuration"
    assert item["agent_is_default"] is False
    assert item["sidebar_has_chat"] is True
    assert item["agent_label"]


@pytest.mark.requisito("RF-018")
def test_row_is_empty():
    key = _main_view(_SEC_MAIN).key
    assert _row_is_empty(
        AdminSectionOverride(section_id=_SEC_MAIN, agent_profile_id=None, views=None)
    ) is True
    assert _row_is_empty(
        AdminSectionOverride(section_id=_SEC_MAIN, agent_profile_id=None, views={})
    ) is True
    # override vacío explícito → NO es una fila vacía (lleva intención del operador)
    assert _row_is_empty(
        AdminSectionOverride(
            section_id=_SEC_MAIN, agent_profile_id=None, views={key: {"sidebar_body": ""}}
        )
    ) is False
    assert _row_is_empty(
        AdminSectionOverride(
            section_id=_SEC_MAIN, agent_profile_id="agent_configuration", views=None
        )
    ) is False


@pytest.mark.requisito("RNF-002")
def test_multi_view_section_default_agent_is_l2():
    spec = get_section_spec(_SEC_MULTI)
    item = _serialize(spec, None)
    assert item["agent_profile_id"] == "agent_configuration"
    assert item["sidebar_has_chat"] is True
    assert len(item["views"]) == len(spec.views)
