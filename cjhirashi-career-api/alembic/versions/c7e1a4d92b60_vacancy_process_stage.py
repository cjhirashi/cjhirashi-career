"""Vacancies: process_stage (replaces application_status) + process_stage_updated_at.

Spec 007. Renames `application_status` -> `process_stage` (and its index),
backfills NULL -> 'not_applied', makes it NOT NULL with default, adds
`process_stage_updated_at` (backfilled from updated_at/created_at/now()) and a
CHECK constraint with the 13-stage catalog.

Idempotent (inspects the current state) and transactional (PG DDL). A
preflight aborts, before any DDL, if the stage column holds values outside the
catalog. The catalog is copied literally on purpose: a migration must not
import the live catalog (it may change later); a unit test compares this copy
with the spec contract.

Revision ID: c7e1a4d92b60
Revises: a9b1c2d3e4f5
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c7e1a4d92b60"
down_revision: Union[str, None] = "a9b1c2d3e4f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "vacancies"
_CHECK = "ck_vacancies_process_stage"
_OLD_INDEX = "ix_vacancies_application_status"
_NEW_INDEX = "ix_vacancies_process_stage"
_STAGES = (
    "not_applied",
    "applied",
    "screening",
    "hr_interview",
    "technical_interview",
    "technical_test",
    "final_interview",
    "offer",
    "hiring_process",
    "hired",
    "rejected",
    "withdrawn",
    "no_response",
)
_STAGES_SQL = ", ".join(f"'{s}'" for s in _STAGES)


def _columns(inspector) -> set:
    return {c["name"] for c in inspector.get_columns(_TABLE)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = _columns(inspector)

    # 1. Preflight (RF-008): antes de cualquier DDL.
    source = "application_status" if "application_status" in columns else "process_stage"
    if source in columns:
        rows = bind.execute(
            sa.text(
                f"SELECT DISTINCT {source} FROM {_TABLE} "
                f"WHERE {source} IS NOT NULL AND {source} NOT IN ({_STAGES_SQL})"
            )
        ).fetchall()
        if rows:
            bad = sorted(str(r[0]) for r in rows)
            raise RuntimeError(
                f"{_TABLE}.{source} contiene valores fuera del catálogo de etapas: {bad}. "
                "Corrígelos antes de migrar."
            )

    # 2. Renombrar columna e índice.
    if "application_status" in columns and "process_stage" not in columns:
        op.execute(f"ALTER TABLE {_TABLE} RENAME COLUMN application_status TO process_stage")
        op.execute(f"ALTER INDEX IF EXISTS {_OLD_INDEX} RENAME TO {_NEW_INDEX}")
    op.execute(f"CREATE INDEX IF NOT EXISTS {_NEW_INDEX} ON {_TABLE} (process_stage)")

    # 3. NULL -> not_applied, default y NOT NULL (RF-007).
    op.execute(f"UPDATE {_TABLE} SET process_stage = 'not_applied' WHERE process_stage IS NULL")
    op.execute(f"ALTER TABLE {_TABLE} ALTER COLUMN process_stage SET DEFAULT 'not_applied'")
    op.execute(f"ALTER TABLE {_TABLE} ALTER COLUMN process_stage SET NOT NULL")

    # 4. Fecha de entrada a la etapa (RF-024).
    op.execute(f"ALTER TABLE {_TABLE} ADD COLUMN IF NOT EXISTS process_stage_updated_at TIMESTAMP WITH TIME ZONE")
    op.execute(
        f"UPDATE {_TABLE} SET process_stage_updated_at = COALESCE(updated_at, created_at, now()) "
        "WHERE process_stage_updated_at IS NULL"
    )
    op.execute(f"ALTER TABLE {_TABLE} ALTER COLUMN process_stage_updated_at SET DEFAULT now()")
    op.execute(f"ALTER TABLE {_TABLE} ALTER COLUMN process_stage_updated_at SET NOT NULL")

    # 5. CHECK con el catálogo (RF-006).
    checks = {c["name"] for c in inspector.get_check_constraints(_TABLE)}
    if _CHECK not in checks:
        op.execute(
            f"ALTER TABLE {_TABLE} ADD CONSTRAINT {_CHECK} "
            f"CHECK (process_stage IN ({_STAGES_SQL}))"
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = _columns(inspector)

    op.execute(f"ALTER TABLE {_TABLE} DROP CONSTRAINT IF EXISTS {_CHECK}")
    op.execute(f"ALTER TABLE {_TABLE} DROP COLUMN IF EXISTS process_stage_updated_at")
    if "process_stage" in columns and "application_status" not in columns:
        # Los NULL convertidos a 'not_applied' no se restauran (pérdida aceptada).
        op.execute(f"ALTER TABLE {_TABLE} ALTER COLUMN process_stage DROP NOT NULL")
        op.execute(f"ALTER TABLE {_TABLE} ALTER COLUMN process_stage DROP DEFAULT")
        op.execute(f"ALTER INDEX IF EXISTS {_NEW_INDEX} RENAME TO {_OLD_INDEX}")
        op.execute(f"ALTER TABLE {_TABLE} RENAME COLUMN process_stage TO application_status")
