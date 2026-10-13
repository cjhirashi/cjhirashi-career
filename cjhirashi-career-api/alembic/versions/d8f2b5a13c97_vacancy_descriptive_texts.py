"""Vacancies: four descriptive long-text columns.

Spec 008. Adds `company_overview`, `candidate_profile`, `offer_summary` and
`work_culture` (TEXT, NULL, no default, no backfill): existing rows stay NULL.

Idempotent (adds only the columns that are missing) and transactional (PG DDL).
`downgrade()` drops the four columns and therefore LOSES their content.

Revision ID: d8f2b5a13c97
Revises: c7e1a4d92b60
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d8f2b5a13c97"
down_revision: Union[str, None] = "c7e1a4d92b60"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "vacancies"
_COLUMNS = ("company_overview", "candidate_profile", "offer_summary", "work_culture")


def _existing() -> set:
    inspector = sa.inspect(op.get_bind())
    return {c["name"] for c in inspector.get_columns(_TABLE)}


def upgrade() -> None:
    existing = _existing()
    for name in _COLUMNS:
        if name not in existing:
            op.execute(f"ALTER TABLE {_TABLE} ADD COLUMN {name} TEXT NULL")


def downgrade() -> None:
    existing = _existing()
    for name in _COLUMNS:
        if name in existing:
            op.execute(f"ALTER TABLE {_TABLE} DROP COLUMN {name}")
