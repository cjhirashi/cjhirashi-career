"""Retira el descubrimiento de vacantes: columnas de board en target_companies

Revision ID: 9e5a3b7d2c04
Revises: 8d4f2a6c1e93
Create Date: 2026-11-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "9e5a3b7d2c04"
down_revision: Union[str, None] = "8d4f2a6c1e93"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("target_companies_career_board_provider_check", "target_companies", type_="check")
    op.drop_column("target_companies", "career_board_token")
    op.drop_column("target_companies", "career_board_provider")


def downgrade() -> None:
    op.add_column("target_companies", sa.Column("career_board_provider", sa.String(length=30), nullable=True))
    op.add_column("target_companies", sa.Column("career_board_token", sa.String(length=100), nullable=True))
    op.create_check_constraint(
        "target_companies_career_board_provider_check",
        "target_companies",
        "career_board_provider IS NULL OR career_board_provider IN ('greenhouse', 'lever')",
    )
