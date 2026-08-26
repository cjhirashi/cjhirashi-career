"""Add scheduling and assignee fields to bedrock_tasks (ADR-015).

Revision ID: f6a7b8c9d0e1
Revises: a6b7c8d9e0f1
Create Date: 2026-08-26
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, tuple, None] = "a6b7c8d9e0f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "bedrock_tasks",
        sa.Column("assignee_type", sa.String(length=20), nullable=False, server_default="user"),
    )
    op.add_column("bedrock_tasks", sa.Column("agent_profile_id", sa.String(length=50), nullable=True))
    op.add_column("bedrock_tasks", sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("bedrock_tasks", sa.Column("due_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "bedrock_tasks",
        sa.Column("priority", sa.String(length=20), nullable=False, server_default="medium"),
    )
    op.add_column("bedrock_tasks", sa.Column("execution_result", sa.Text(), nullable=True))
    op.add_column("bedrock_tasks", sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("bedrock_tasks", sa.Column("error_message", sa.Text(), nullable=True))
    op.create_index("ix_bedrock_tasks_assignee_type", "bedrock_tasks", ["assignee_type"])
    op.create_index("ix_bedrock_tasks_scheduled_at", "bedrock_tasks", ["scheduled_at"])
    op.create_index(
        "ix_bedrock_tasks_scheduler",
        "bedrock_tasks",
        ["assignee_type", "status", "scheduled_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_bedrock_tasks_scheduler", table_name="bedrock_tasks")
    op.drop_index("ix_bedrock_tasks_scheduled_at", table_name="bedrock_tasks")
    op.drop_index("ix_bedrock_tasks_assignee_type", table_name="bedrock_tasks")
    op.drop_column("bedrock_tasks", "error_message")
    op.drop_column("bedrock_tasks", "executed_at")
    op.drop_column("bedrock_tasks", "execution_result")
    op.drop_column("bedrock_tasks", "priority")
    op.drop_column("bedrock_tasks", "due_at")
    op.drop_column("bedrock_tasks", "scheduled_at")
    op.drop_column("bedrock_tasks", "agent_profile_id")
    op.drop_column("bedrock_tasks", "assignee_type")
