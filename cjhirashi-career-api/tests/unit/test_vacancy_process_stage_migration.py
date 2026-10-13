"""Spec 007 · RF-006..RF-009, RF-024 — migración `c7e1a4d92b60`.

Se prueba con dobles (sin BD): orden de pasos, preflight, idempotencia y
downgrade. El comportamiento contra Postgres real se verifica en T-042.
"""
import importlib.util
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_MIGRATION = _ROOT / "alembic" / "versions" / "c7e1a4d92b60_vacancy_process_stage.py"
_CONTRACT = (
    _ROOT.parent / ".harness" / "specs" / "007-vacantes-etapa-y-estado"
    / "contracts" / "process-stage-catalog.json"
)
CATALOG_VALUES = [s["value"] for s in json.loads(_CONTRACT.read_text(encoding="utf-8"))["stages"]]


def _load():
    spec = importlib.util.spec_from_file_location("_mig_c7e1a4d92b60", _MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Harness:
    """Registra, en orden, bind.execute (preflight) y op.* de una migración."""

    def __init__(self, mod, *, columns, checks=(), invalid=()):
        self.mod = mod
        self.calls = []  # (tipo, texto)
        inspector = MagicMock()
        inspector.get_columns.return_value = [{"name": c} for c in columns]
        inspector.get_check_constraints.return_value = [{"name": c} for c in checks]
        self.inspector = inspector
        bind = MagicMock()

        def _bind_exec(stmt, params=None):
            self.calls.append(("bind", str(stmt)))
            res = MagicMock()
            res.fetchall.return_value = [(v,) for v in invalid]
            return res

        bind.execute.side_effect = _bind_exec
        self.bind = bind

    def run(self, fn_name):
        op = MagicMock()
        op.get_bind.return_value = self.bind
        op.execute.side_effect = lambda stmt, *a, **k: self.calls.append(("op", str(stmt)))
        with patch.object(self.mod, "op", op), patch.object(
            self.mod.sa, "inspect", return_value=self.inspector
        ):
            getattr(self.mod, fn_name)()

    def sql(self):
        return [c[1].upper() for c in self.calls if c[0] == "op"]

    def index_of(self, *needles):
        needles = [n.upper() for n in needles]
        for i, text_ in enumerate(self.sql()):
            if all(n in text_ for n in needles):
                return i
        raise AssertionError(f"no hay paso con {needles}: {self.sql()}")


OLD_COLS = ["id", "application_status", "created_at", "updated_at"]
NEW_COLS = ["id", "process_stage", "process_stage_updated_at", "created_at", "updated_at"]


@pytest.mark.requisito("RF-006")
def test_revision_chain():
    mod = _load()
    assert mod.revision == "c7e1a4d92b60"
    assert mod.down_revision == "a9b1c2d3e4f5"
    assert mod.branch_labels is None


@pytest.mark.requisito("RF-006")
def test_literal_catalog_copy_matches_contract():
    mod = _load()
    assert list(mod._STAGES) == CATALOG_VALUES


@pytest.mark.requisito("RF-008")
def test_preflight_with_foreign_value_raises_before_any_ddl():
    mod = _load()
    h = _Harness(mod, columns=OLD_COLS, invalid=["foo"])
    with pytest.raises(RuntimeError, match="foo"):
        h.run("upgrade")
    assert h.sql() == []  # ningún ALTER/CREATE/UPDATE antes del fallo
    assert h.calls and h.calls[0][0] == "bind"


@pytest.mark.requisito("RF-008")
def test_preflight_uses_existing_column_name_and_checks_catalog():
    mod = _load()
    h = _Harness(mod, columns=NEW_COLS)
    h.run("upgrade")
    pre = h.calls[0][1]
    assert h.calls[0][0] == "bind"
    assert "process_stage" in pre and "application_status" not in pre
    assert all(f"'{v}'" in pre for v in CATALOG_VALUES)


@pytest.mark.requisito("RF-007")
@pytest.mark.requisito("RF-024")
@pytest.mark.requisito("RF-006")
def test_upgrade_step_order_from_old_schema():
    mod = _load()
    h = _Harness(mod, columns=OLD_COLS)
    h.run("upgrade")
    rename = h.index_of("RENAME COLUMN", "APPLICATION_STATUS", "PROCESS_STAGE")
    fill_null = h.index_of("UPDATE", "PROCESS_STAGE", "'NOT_APPLIED'", "IS NULL")
    not_null = h.index_of("ALTER COLUMN PROCESS_STAGE", "SET NOT NULL")
    add_date = h.index_of("PROCESS_STAGE_UPDATED_AT", "ADD COLUMN")
    fill_date = h.index_of("UPDATE", "COALESCE(UPDATED_AT, CREATED_AT, NOW())")
    date_not_null = h.index_of("ALTER COLUMN PROCESS_STAGE_UPDATED_AT", "SET NOT NULL")
    check = h.index_of("ADD CONSTRAINT CK_VACANCIES_PROCESS_STAGE", "CHECK")
    assert rename < fill_null < not_null
    assert add_date < fill_date < date_not_null
    assert max(rename, fill_null, not_null, add_date, fill_date, date_not_null) < check
    assert h.index_of("ALTER INDEX", "IX_VACANCIES_APPLICATION_STATUS", "IX_VACANCIES_PROCESS_STAGE") > rename
    assert h.index_of("SET DEFAULT 'NOT_APPLIED'") < not_null
    assert h.index_of("SET DEFAULT NOW()") < date_not_null


@pytest.mark.requisito("RF-006")
def test_upgrade_check_contains_all_catalog_values():
    mod = _load()
    h = _Harness(mod, columns=OLD_COLS)
    h.run("upgrade")
    check_sql = h.sql()[h.index_of("ADD CONSTRAINT CK_VACANCIES_PROCESS_STAGE")]
    assert all(f"'{v}'".upper() in check_sql for v in CATALOG_VALUES)


@pytest.mark.requisito("RF-007")
def test_upgrade_is_idempotent_when_already_migrated():
    mod = _load()
    h = _Harness(mod, columns=NEW_COLS, checks=["ck_vacancies_process_stage"])
    h.run("upgrade")
    sql = " ; ".join(h.sql())
    assert "RENAME COLUMN" not in sql
    assert "ADD CONSTRAINT" not in sql
    # los pasos IF NOT EXISTS / WHERE ... IS NULL son seguros de repetir
    assert "ADD COLUMN IF NOT EXISTS" in sql or "ADD COLUMN" not in sql


@pytest.mark.requisito("RF-009")
def test_downgrade_reverses_in_order():
    mod = _load()
    h = _Harness(mod, columns=NEW_COLS, checks=["ck_vacancies_process_stage"])
    h.run("downgrade")
    drop_check = h.index_of("DROP CONSTRAINT", "CK_VACANCIES_PROCESS_STAGE")
    drop_date = h.index_of("DROP COLUMN", "PROCESS_STAGE_UPDATED_AT")
    rel = h.index_of("ALTER COLUMN PROCESS_STAGE", "DROP NOT NULL")
    rename = h.index_of("RENAME COLUMN", "PROCESS_STAGE", "APPLICATION_STATUS")
    assert drop_check < drop_date < rel < rename
    assert h.index_of("ALTER INDEX", "IX_VACANCIES_PROCESS_STAGE", "IX_VACANCIES_APPLICATION_STATUS") > 0
    assert h.index_of("ALTER COLUMN PROCESS_STAGE", "DROP DEFAULT") < rename


@pytest.mark.requisito("RF-009")
def test_downgrade_is_idempotent_when_already_reverted():
    mod = _load()
    h = _Harness(mod, columns=OLD_COLS)
    h.run("downgrade")
    assert not any("RENAME COLUMN" in s for s in h.sql())
