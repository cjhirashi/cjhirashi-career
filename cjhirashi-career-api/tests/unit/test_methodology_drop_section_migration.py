"""Spec 005 · RF-001 / RF-017 / RF-019 — la migración que retira el texto libre
`operational_methodologies.section` / `subsection` / `notes`:

  (a) hace `DROP COLUMN IF EXISTS` de los 3 campos + `DROP INDEX IF EXISTS` del
      índice de `section`, y **no** toca `section_ids` (RF-001 idempotente, RF-019
      sin backfill);
  (b) vuelca `id`, `user_id`, `section`, `subsection`, `notes` a
      `operational_methodologies_freeform_backup` (`CREATE TABLE IF NOT EXISTS`
      -> `INSERT ... SELECT`) **antes** de cualquier `DROP COLUMN` (RF-017);
  (c) un segundo `upgrade()` no falla — toda la DDL va guardada con
      `IF [NOT] EXISTS` (RF-001);
  (d) el id de revisión no existe ya en `alembic/versions/` y encadena de
      `b3d4e5f6a7c8` (migración de la feature 004).

Patrón de test (plan.md §5.1 "Migración — unit, DB doble"): `op` / `bind`
mockeados; la aserción es sobre el SQL emitido y su orden, no sobre una
ejecución real contra Postgres. Mismo enfoque que
`test_methodology_section_ids_migration.py` (004).
"""
import importlib.util
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_VERSIONS_DIR = Path(__file__).resolve().parents[2] / "alembic" / "versions"
_MIGRATION = _VERSIONS_DIR / "c5d6e7f8a9b0_methodology_drop_section_freeform.py"


def _load():
    spec = importlib.util.spec_from_file_location("_mig_c5d6e7f8a9b0", _MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_upgrade(mod):
    """Corre ``upgrade()`` con ``op`` / ``bind`` mockeados.

    Devuelve la lista ordenada de SQL emitido vía ``op.execute(...)``.
    """
    emitted: list[str] = []

    fake_bind = MagicMock()
    fake_bind.execute.return_value = MagicMock(fetchall=lambda: [])

    def _execute(stmt, *args, **kwargs):
        emitted.append(str(stmt))
        return MagicMock(fetchall=lambda: [])

    with patch.object(mod, "op") as op:
        op.execute.side_effect = _execute
        op.get_bind.return_value = fake_bind
        mod.upgrade()

    return emitted


# ---------------------------------------------------------------------------
# (a) DROP idempotente de los 3 campos + índice; section_ids intacto
# ---------------------------------------------------------------------------
@pytest.mark.requisito("RF-001")
@pytest.mark.requisito("RF-019")
def test_a_drops_freeform_columns_and_index_keeps_section_ids():
    mod = _load()
    up = [s.upper() for s in _run_upgrade(mod)]

    for col in ("SECTION", "SUBSECTION", "NOTES"):
        assert any(
            f"DROP COLUMN IF EXISTS {col}" in s for s in up
        ), f"falta DROP COLUMN IF EXISTS {col}"

    assert any(
        "DROP INDEX IF EXISTS" in s and "IX_OPERATIONAL_METHODOLOGIES_SECTION" in s
        for s in up
    ), "falta DROP INDEX IF EXISTS ix_operational_methodologies_section"

    # RF-019: nada escribe ni elimina section_ids (sin backfill, columna intacta)
    for s in up:
        assert "DROP COLUMN IF EXISTS SECTION_IDS" not in s, s
        assert not (
            "UPDATE OPERATIONAL_METHODOLOGIES" in s and "SECTION_IDS" in s
        ), s


# ---------------------------------------------------------------------------
# (b) respaldo del texto libre ANTES del DROP
# ---------------------------------------------------------------------------
@pytest.mark.requisito("RF-017")
def test_b_freeform_backup_table_populated_before_drop():
    mod = _load()
    emitted = _run_upgrade(mod)
    up = [s.upper() for s in emitted]

    create_idx = next(
        i for i, s in enumerate(up)
        if "CREATE TABLE" in s and "OPERATIONAL_METHODOLOGIES_FREEFORM_BACKUP" in s
    )
    assert "IF NOT EXISTS" in up[create_idx]

    insert_idx = next(
        i for i, s in enumerate(up)
        if "INSERT INTO" in s and "OPERATIONAL_METHODOLOGIES_FREEFORM_BACKUP" in s
    )
    ins = up[insert_idx]
    for col in ("ID", "USER_ID", "SECTION", "SUBSECTION", "NOTES"):
        assert col in ins, f"el volcado no incluye {col}"
    assert "SELECT" in ins and "FROM OPERATIONAL_METHODOLOGIES" in ins

    drop_idxs = [i for i, s in enumerate(up) if "DROP COLUMN" in s]
    assert drop_idxs, "se esperaba al menos un DROP COLUMN"
    assert create_idx < min(drop_idxs), "CREATE TABLE backup debe ir antes del DROP"
    assert insert_idx < min(drop_idxs), "INSERT ... SELECT debe ir antes del DROP"


# ---------------------------------------------------------------------------
# (c) idempotencia: segundo upgrade no falla, DDL guardada con IF [NOT] EXISTS
# ---------------------------------------------------------------------------
@pytest.mark.requisito("RF-001")
def test_c_second_upgrade_is_idempotent():
    mod = _load()
    first = _run_upgrade(mod)
    second = _run_upgrade(mod)  # no debe lanzar
    assert second == first

    for s in [x.upper() for x in first]:
        if "CREATE TABLE" in s:
            assert "IF NOT EXISTS" in s, s
        if "DROP COLUMN" in s:
            assert "IF EXISTS" in s, s
        if "DROP INDEX" in s:
            assert "IF EXISTS" in s, s


# ---------------------------------------------------------------------------
# (d) id de revisión único + encadena de la 004
# ---------------------------------------------------------------------------
@pytest.mark.requisito("RF-001")
def test_d_revision_id_is_unique_and_chains_from_004():
    mod = _load()
    assert mod.revision == "c5d6e7f8a9b0"
    assert mod.down_revision == "b3d4e5f6a7c8"
    assert mod.branch_labels is None

    seen: set[str] = set()
    for path in _VERSIONS_DIR.glob("*.py"):
        if path.name == _MIGRATION.name:
            continue
        for m in re.finditer(
            r'^revision(?:: *str)? *= *["\']([0-9a-f]+)["\']',
            path.read_text(),
            re.MULTILINE,
        ):
            seen.add(m.group(1))

    assert mod.revision not in seen, (
        f"el id de revisión {mod.revision} ya está en uso en alembic/versions/"
    )
