"""Competencies: retira is_highlighted (sin uso; la home se controla con featured_on_home).

El downgrade recrea la columna con FALSE; los valores previos se recuperan del respaldo.

Revision ID: 7c3e1d9a5b82
Revises: 6b2d8f4a1c57
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "7c3e1d9a5b82"
down_revision: Union[str, None] = "6b2d8f4a1c57"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("competencies", "is_highlighted")


def downgrade() -> None:
    op.add_column("competencies", sa.Column("is_highlighted", sa.Boolean(), server_default=sa.false(), nullable=True))
