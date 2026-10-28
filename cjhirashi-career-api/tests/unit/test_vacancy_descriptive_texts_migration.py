"""Spec 008 · RF-007 — migración `d8f2b5a13c97` (cuatro columnas de texto en `vacancies`).

Con dobles (sin BD): cadena de revisiones, ADD/DROP COLUMN, idempotencia y ausencia de
UPDATE. El comportamiento contra Postgres se verifica en T-042.
"""
import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_VERSIONS = _ROOT / "alembic" / "versions"
_MIGRATION = _VERSIONS / "d8f2b5a13c97_vacancy_descriptive_texts.py"
FIELDS = ("company_overview", "candidate_profile", "offer_summary", "work_culture")
BASE_COLS = ["id", "company", "analysis_notes"]


def _load():
    spec = importlib.util.spec_from_file_location("_mig_d8f2b5a13c97", _MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run(fn_name, columns):
    mod = _load()
    inspector = MagicMock()
    inspector.get_columns.return_value = [{"name": c} for c in columns]
    calls = []
    op = MagicMock()
    op.get_bind.return_value = MagicMock()
    op.execute.side_effect = lambda stmt, *a, **k: calls.append(str(stmt).upper())
    with patch.object(mod, "op", op), patch.object(mod.sa, "inspect", return_value=inspector):
        getattr(mod, fn_name)()
    return calls


@pytest.mark.requisito("RF-007")
def test_revision_chain_and_single_head():
    mod = _load()
    assert mod.revision == "d8f2b5a13c97"
    assert mod.down_revision == "c7e1a4d92b60"
    assert mod.branch_labels is None
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    cfg = Config()
    cfg.set_main_option("script_location", str(_ROOT / "alembic"))
    # No pinning the exact head id: that breaks on every later migration. The
    # actual invariant worth checking is a single linear chain (no branching).
    assert len(ScriptDirectory.from_config(cfg).get_heads()) == 1


@pytest.mark.requisito("RF-007")
def test_upgrade_adds_the_four_text_columns_nullable_without_update():
    sql = _run("upgrade", BASE_COLS)
    for f in FIELDS:
        adds = [s for s in sql if "ADD COLUMN" in s and f.upper() in s]
        assert len(adds) == 1 and "TEXT" in adds[0] and "NOT NULL" not in adds[0]
        assert "DEFAULT" not in adds[0]
    assert not any("UPDATE" in s for s in sql)


@pytest.mark.requisito("RF-007")
def test_upgrade_is_idempotent_and_adds_only_missing_columns():
    assert _run("upgrade", BASE_COLS + list(FIELDS)) == []
    sql = _run("upgrade", BASE_COLS + ["company_overview", "work_culture"])
    assert len(sql) == 2
    assert any("CANDIDATE_PROFILE" in s for s in sql) and any("OFFER_SUMMARY" in s for s in sql)


@pytest.mark.requisito("RF-007")
def test_downgrade_drops_the_four_columns_only_if_they_exist():
    sql = _run("downgrade", BASE_COLS + list(FIELDS))
    for f in FIELDS:
        assert len([s for s in sql if "DROP COLUMN" in s and f.upper() in s]) == 1
    assert _run("downgrade", BASE_COLS) == []
    assert len(_run("downgrade", BASE_COLS + ["offer_summary"])) == 1
