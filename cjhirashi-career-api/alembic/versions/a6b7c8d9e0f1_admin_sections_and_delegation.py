"""Add admin section overrides and editable agent delegation targets.

Revision ID: a6b7c8d9e0f1
Revises: e5f6a7b8c9d0, c2d3e4f5a6b7
Create Date: 2026-08-26
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "a6b7c8d9e0f1"
down_revision: Union[str, tuple, None] = ("e5f6a7b8c9d0", "c2d3e4f5a6b7")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admin_section_overrides",
        sa.Column("section_id", sa.String(length=80), primary_key=True),
        sa.Column("agent_profile_id", sa.String(length=50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("views", JSONB(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_table(
        "bedrock_agent_delegation",
        sa.Column("profile_id", sa.String(length=50), primary_key=True),
        sa.Column("target_ids", JSONB(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("bedrock_agent_delegation")
    op.drop_table("admin_section_overrides")
