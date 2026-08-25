"""Per-agent conversation history — agent_profile_id on bedrock_conversations.

Revision ID: a8b9c0d1e2f3
Revises: f5b6c7d8e9f0
Create Date: 2026-08-24
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a8b9c0d1e2f3"
down_revision: Union[str, None] = "f5b6c7d8e9f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "bedrock_conversations",
        sa.Column("agent_profile_id", sa.String(length=50), nullable=True),
    )
    op.create_index(
        "ix_bedrock_conversations_agent_profile_id",
        "bedrock_conversations",
        ["agent_profile_id"],
    )
    op.create_index(
        "ix_bedrock_conversations_user_type_profile",
        "bedrock_conversations",
        ["user_id", "session_type", "agent_profile_id"],
    )
    # Chat general always belongs to the orchestrator. Contextual rows stay NULL
    # so they do not reappear as a shared list under a single specialist.
    op.execute(
        "UPDATE bedrock_conversations "
        "SET agent_profile_id = 'orchestrator' "
        "WHERE session_type = 'general' AND agent_profile_id IS NULL"
    )


def downgrade() -> None:
    op.drop_index("ix_bedrock_conversations_user_type_profile", table_name="bedrock_conversations")
    op.drop_index("ix_bedrock_conversations_agent_profile_id", table_name="bedrock_conversations")
    op.drop_column("bedrock_conversations", "agent_profile_id")
