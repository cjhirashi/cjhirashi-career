"""Add career board fields to target_companies

Greenhouse/Lever public board token so job discovery can list
open roles at a target company without scraping.

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-08-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("target_companies", sa.Column("career_board_provider", sa.String(length=30), nullable=True))
    op.add_column("target_companies", sa.Column("career_board_token", sa.String(length=100), nullable=True))
    op.create_check_constraint(
        "target_companies_career_board_provider_check",
        "target_companies",
        "career_board_provider IS NULL OR career_board_provider IN ('greenhouse', 'lever')",
    )


def downgrade() -> None:
    op.drop_constraint("target_companies_career_board_provider_check", "target_companies", type_="check")
    op.drop_column("target_companies", "career_board_token")
    op.drop_column("target_companies", "career_board_provider")
