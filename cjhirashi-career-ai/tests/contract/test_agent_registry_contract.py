"""RF-012 / RF-001: el registro de perfiles del harness coincide con contracts/agent-registry.json (T-068)."""
import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.requisito("RF-012")

CONTRACT = (
    Path(__file__).resolve().parents[3]
    / ".harness" / "specs" / "009-harness-agentes-fuera-de-api" / "contracts" / "agent-registry.json"
)


def _canon() -> dict:
    assert CONTRACT.is_file(), f"falta el contrato {CONTRACT}"
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    return {p["id"]: (p["label"], p["level"]) for p in data["profiles"]}


def test_el_contrato_declara_veinte_perfiles():
    assert len(_canon()) == 20


def test_registro_coincide_con_el_contrato_en_id_label_y_nivel():
    from services.agent_registry import registry_entries

    actual = {e.id: (e.label, e.level) for e in registry_entries()}
    assert actual == _canon()


def test_registro_no_tiene_ids_duplicados():
    from services.agent_registry import registry_entries

    ids = [e.id for e in registry_entries()]
    assert len(ids) == len(set(ids)) == 20


def test_registro_sale_de_la_misma_fuente_que_los_perfiles():
    from services import agent_profiles
    from services.agent_registry import known_profile_ids, registry_entries

    assert known_profile_ids() == set(agent_profiles.known_agent_profile_ids())
    assert [e.id for e in registry_entries()] == [p.id for p in agent_profiles.list_profiles()]


def test_cada_perfil_conserva_el_nivel_canonico_y_su_record_id():
    from services import agent_profiles

    canon = _canon()
    for profile in agent_profiles.list_profiles():
        assert profile.level == canon[profile.id][1]
        assert agent_profiles.get_profile(agent_profiles.agent_record_id(profile.id)).id == profile.id
