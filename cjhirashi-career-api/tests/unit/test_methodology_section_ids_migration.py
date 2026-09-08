"""Spec 004 · RF-013 — la migración añade `operational_methodologies.section_ids`
de forma idempotente y retira los ids de nivel 2 de `agent_profile_ids`, dejando
intactos los de nivel 1 y 3.
"""
import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "alembic"
    / "versions"
    / "b3d4e5f6a7c8_methodology_section_ids.py"
)


def _load():
    spec = importlib.util.spec_from_file_location("_mig_b3d4e5f6a7c8", _MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.requisito("RF-013")
def test_revision_chains_from_003():
    mod = _load()
    assert mod.revision == "b3d4e5f6a7c8"
    assert mod.down_revision == "f7a8b9c0d1e2"  # str → lineal
    assert mod.branch_labels is None


@pytest.mark.requisito("RF-013")
def test_upgrade_adds_column_if_not_exists_and_strips_l2():
    mod = _load()

    # fila con mezcla L2 + L3; otra sólo L3; otra sólo L2
    stored = {
        "opm-1": ["agent_professional_identity", "agent_visual_design"],  # L2 + L3
        "opm-2": ["agent_visual_design"],                                  # L3
        "opm-3": ["agent_search_operations"],                             # L2
    }
    updates = {}

    fake_bind = MagicMock()

    def _execute(stmt, params=None):
        sql = str(stmt).upper()
        if sql.startswith("SELECT"):
            res = MagicMock()
            res.fetchall.return_value = list(stored.items())
            return res
        if "UPDATE" in sql:
            import json as _j
            updates[params["id"]] = _j.loads(params["v"])
            return MagicMock()
        return MagicMock()

    fake_bind.execute.side_effect = _execute

    with patch.object(mod, "op") as op:
        op.get_bind.return_value = fake_bind
        mod.upgrade()

    # 1ª llamada: ADD COLUMN IF NOT EXISTS section_ids
    add_sql = op.execute.call_args_list[0].args[0].upper()
    assert "ADD COLUMN IF NOT EXISTS SECTION_IDS" in add_sql
    assert "OPERATIONAL_METHODOLOGIES" in add_sql

    # se limpian los ids L2, se conservan L1/L3
    assert updates["opm-1"] == ["agent_visual_design"]
    assert updates["opm-3"] == []
    assert "opm-2" not in updates  # sin ids L2 → no se toca


@pytest.mark.requisito("RF-013")
def test_downgrade_drops_column_if_exists():
    mod = _load()
    with patch.object(mod, "op") as op:
        mod.downgrade()
    sql = op.execute.call_args.args[0].upper()
    assert "DROP COLUMN IF EXISTS SECTION_IDS" in sql


@pytest.mark.requisito("RF-013")
def test_model_has_section_ids_column():
    from models.operational_methodology import OperationalMethodology

    assert "section_ids" in OperationalMethodology.__table__.columns
