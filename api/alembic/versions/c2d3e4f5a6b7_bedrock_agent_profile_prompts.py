"""bedrock_agent_profile_prompts — per-agent prompt suffix overrides

Revision ID: c2d3e4f5a6b7
Revises: b7c8d9e0f1a2
Create Date: 2026-08-24
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c2d3e4f5a6b7"
down_revision: Union[str, None] = "b7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "bedrock_agent_profile_prompts",
        sa.Column("profile_id", sa.String(50), nullable=False),
        sa.Column("system_prompt_suffix", sa.Text(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("profile_id"),
    )


def downgrade() -> None:
    op.drop_table("bedrock_agent_profile_prompts")
