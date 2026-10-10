"""Add role_gap_analysis.target_date (checklist Paulina #9).

Only `closure_status` existed before - no way to track a deadline for
closing the gap.

Revision ID: d6e7f8a9b1c2
Revises: c5d6e7f8a9b1
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d6e7f8a9b1c2"
down_revision: Union[str, None] = "c5d6e7f8a9b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "role_gap_analysis"


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns(_TABLE)}
    if "target_date" not in columns:
        op.add_column(_TABLE, sa.Column("target_date", sa.Date(), nullable=True))


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns(_TABLE)}
    if "target_date" in columns:
        op.drop_column(_TABLE, "target_date")
