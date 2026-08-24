"""Bedrock local harness — settings extendidos, session_type, round logs, PDF templates

Revision ID: a1b2c3d4e5f6
Revises: 9c4d7e1f2a8b
Create Date: 2026-08-23
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "9c4d7e1f2a8b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("bedrock_settings", sa.Column("active_model_id", sa.String(150), nullable=True))
    op.add_column("bedrock_settings", sa.Column("orchestrator_model_id", sa.String(150), nullable=True))
    op.add_column(
        "bedrock_settings",
        sa.Column("max_round_trips", sa.Integer(), nullable=False, server_default="6"),
    )
    op.add_column(
        "bedrock_settings",
        sa.Column("history_window", sa.Integer(), nullable=False, server_default="20"),
    )
    op.add_column(
        "bedrock_settings",
        sa.Column("daily_budget_usd", sa.Numeric(10, 4), nullable=False, server_default="5.0"),
    )

    op.add_column(
        "bedrock_conversations",
        sa.Column("session_type", sa.String(20), nullable=False, server_default="contextual"),
    )
    op.create_index("ix_bedrock_conversations_session_type", "bedrock_conversations", ["session_type"])

    op.create_table(
        "bedrock_usage_round_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(100), nullable=False),
        sa.Column("model_id", sa.String(150), nullable=True),
        sa.Column("round_type", sa.String(30), nullable=False, server_default="converse"),
        sa.Column("tool_name", sa.String(100), nullable=True),
        sa.Column("agent_profile_id", sa.String(50), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_cost_usd", sa.Numeric(12, 6), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bedrock_usage_round_logs_user_id", "bedrock_usage_round_logs", ["user_id"])
    op.create_index("ix_bedrock_usage_round_logs_session_id", "bedrock_usage_round_logs", ["session_id"])
    op.create_index("ix_bedrock_usage_round_logs_created_at", "bedrock_usage_round_logs", ["created_at"])

    op.create_table(
        "pdf_output_templates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("html_template", sa.Text(), nullable=False),
        sa.Column("css_content", sa.Text(), nullable=True),
        sa.Column("variables_schema", postgresql.JSONB(), nullable=True),
        sa.Column("preview_notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pdf_output_templates_user_id", "pdf_output_templates", ["user_id"])
    op.create_index("ix_pdf_output_templates_document_type", "pdf_output_templates", ["document_type"])


def downgrade() -> None:
    op.drop_table("pdf_output_templates")
    op.drop_table("bedrock_usage_round_logs")
    op.drop_index("ix_bedrock_conversations_session_type", table_name="bedrock_conversations")
    op.drop_column("bedrock_conversations", "session_type")
    op.drop_column("bedrock_settings", "daily_budget_usd")
    op.drop_column("bedrock_settings", "history_window")
    op.drop_column("bedrock_settings", "max_round_trips")
    op.drop_column("bedrock_settings", "orchestrator_model_id")
    op.drop_column("bedrock_settings", "active_model_id")
