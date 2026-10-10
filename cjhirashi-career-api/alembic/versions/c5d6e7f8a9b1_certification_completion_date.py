"""Add certifications.completion_date (checklist Paulina #8).

`year` alone cannot order certifications earned in the same year.

Revision ID: c5d6e7f8a9b1
Revises: b4c5d6e7f8a9
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c5d6e7f8a9b1"
down_revision: Union[str, None] = "b4c5d6e7f8a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "certifications"


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns(_TABLE)}
    if "completion_date" not in columns:
        op.add_column(_TABLE, sa.Column("completion_date", sa.Date(), nullable=True))


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns(_TABLE)}
    if "completion_date" in columns:
        op.drop_column(_TABLE, "completion_date")
