"""Add identity.modality_priority and identity.availability_hours (checklist Paulina #7).

Both lived as free text inside `identity.notes` for lack of a dedicated
field; this gives the ordered modality preference and the availability
window their own structured columns.

Revision ID: b4c5d6e7f8a9
Revises: a2b3c4d5e6f7
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b4c5d6e7f8a9"
down_revision: Union[str, None] = "a2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "identity"


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns(_TABLE)}
    if "modality_priority" not in columns:
        op.add_column(_TABLE, sa.Column("modality_priority", postgresql.JSONB(), nullable=True))
    if "availability_hours" not in columns:
        op.add_column(_TABLE, sa.Column("availability_hours", sa.String(length=100), nullable=True))


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns(_TABLE)}
    if "availability_hours" in columns:
        op.drop_column(_TABLE, "availability_hours")
    if "modality_priority" in columns:
        op.drop_column(_TABLE, "modality_priority")
