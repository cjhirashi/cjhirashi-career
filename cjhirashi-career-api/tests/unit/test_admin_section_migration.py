"""feature 001 · RF-021 — la migración que retira ``admin_section_overrides.description``
es DDL mínimo e idempotente (``DROP/ADD COLUMN IF [NOT] EXISTS`` sobre esa única
columna), sin tocar ``views`` ni ``agent_profile_id``, y encadena de forma lineal.
"""
import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest

_MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "alembic"
    / "versions"
    / "c4d5e6f7a8b9_drop_admin_section_override_description.py"
)


def _load():
    spec = importlib.util.spec_from_file_location("_mig_c4d5e6f7a8b9", _MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.requisito("RF-021")
def test_revision_chains_linearly():
    mod = _load()
    assert mod.revision == "c4d5e6f7a8b9"
    assert mod.down_revision == "b2c3d4e5f6a7"  # str, no tupla → sin merge/rama
    assert mod.branch_labels is None


@pytest.mark.requisito("RF-021")
def test_upgrade_drops_only_description_idempotently():
    mod = _load()
    with patch.object(mod, "op") as op:
        mod.upgrade()
    op.execute.assert_called_once()
    sql = op.execute.call_args.args[0].upper()
    assert "DROP COLUMN IF EXISTS DESCRIPTION" in sql
    assert "ADMIN_SECTION_OVERRIDES" in sql
    assert "VIEWS" not in sql and "AGENT_PROFILE_ID" not in sql
    op.drop_column.assert_not_called()
    op.add_column.assert_not_called()
    op.alter_column.assert_not_called()


@pytest.mark.requisito("RF-021")
def test_downgrade_readds_description_nullable():
    mod = _load()
    with patch.object(mod, "op") as op:
        mod.downgrade()
    op.execute.assert_called_once()
    sql = op.execute.call_args.args[0].upper()
    assert "ADD COLUMN IF NOT EXISTS DESCRIPTION TEXT" in sql
    assert "ADMIN_SECTION_OVERRIDES" in sql
    op.drop_column.assert_not_called()
