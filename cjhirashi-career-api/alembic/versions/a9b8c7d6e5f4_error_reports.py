"""Registro centralizado de fallas del sistema (ADR-018).

Revision ID: a9b8c7d6e5f4
Revises: f9a8b7c6d5e4
Create Date: 2026-08-27
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a9b8c7d6e5f4"
down_revision: Union[str, tuple, None] = "f9a8b7c6d5e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("error_reports"):
        op.create_table(
            "error_reports",
            sa.Column("id", sa.String(length=20), primary_key=True),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("source", sa.String(length=255), nullable=False),
            sa.Column("error_type", sa.String(length=120), nullable=True),
            sa.Column("stack_trace", sa.Text(), nullable=True),
            sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("severity", sa.String(length=20), nullable=False, server_default="error"),
            sa.Column("resolved", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("resolution_notes", sa.Text(), nullable=True),
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("resolved_by", sa.String(length=50), nullable=True),
            sa.Column("fingerprint", sa.String(length=64), nullable=False),
            sa.Column("occurrences", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_error_reports_source", "error_reports", ["source"])
        op.create_index("ix_error_reports_resolved", "error_reports", ["resolved"])
        op.create_index("ix_error_reports_fingerprint", "error_reports", ["fingerprint"])
        op.create_index("ix_error_reports_open", "error_reports", ["resolved", "severity", "last_seen_at"])
        op.create_index("ix_error_reports_fp_open", "error_reports", ["fingerprint", "resolved"])
    op.execute(sa.text("CREATE SEQUENCE IF NOT EXISTS err_id_seq START 1"))


def downgrade() -> None:
    op.drop_index("ix_error_reports_fp_open", table_name="error_reports")
    op.drop_index("ix_error_reports_open", table_name="error_reports")
    op.drop_index("ix_error_reports_fingerprint", table_name="error_reports")
    op.drop_index("ix_error_reports_resolved", table_name="error_reports")
    op.drop_index("ix_error_reports_source", table_name="error_reports")
    op.drop_table("error_reports")
    op.execute(sa.text("DROP SEQUENCE IF EXISTS err_id_seq"))
