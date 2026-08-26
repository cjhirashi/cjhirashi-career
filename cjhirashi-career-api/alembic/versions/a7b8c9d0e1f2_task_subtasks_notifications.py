"""Add subtask orchestration fields and user_notifications (ADR-016).

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-08-26
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, tuple, None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_names(table: str) -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table)}


def _index_names(table: str) -> set[str]:
    return {index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table) if index.get("name")}


def _fk_names(table: str) -> set[str]:
    return {fk["name"] for fk in sa.inspect(op.get_bind()).get_foreign_keys(table) if fk.get("name")}


def upgrade() -> None:
    columns = _column_names("bedrock_tasks")
    if "parent_id" not in columns:
        op.add_column("bedrock_tasks", sa.Column("parent_id", sa.String(length=20), nullable=True))
    if "sort_order" not in columns:
        op.add_column(
            "bedrock_tasks",
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        )
    if "is_blocking" not in columns:
        op.add_column(
            "bedrock_tasks",
            sa.Column("is_blocking", sa.Boolean(), nullable=False, server_default=sa.true()),
        )
    if "execute_on_turn" not in columns:
        op.add_column(
            "bedrock_tasks",
            sa.Column("execute_on_turn", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
    if "turn_notified_at" not in columns:
        op.add_column("bedrock_tasks", sa.Column("turn_notified_at", sa.DateTime(timezone=True), nullable=True))

    fks = _fk_names("bedrock_tasks")
    if "fk_bedrock_tasks_parent_id" not in fks:
        op.create_foreign_key(
            "fk_bedrock_tasks_parent_id",
            "bedrock_tasks",
            "bedrock_tasks",
            ["parent_id"],
            ["id"],
            ondelete="CASCADE",
        )
    indexes = _index_names("bedrock_tasks")
    if "ix_bedrock_tasks_parent_id" not in indexes:
        op.create_index("ix_bedrock_tasks_parent_id", "bedrock_tasks", ["parent_id"])
    if "ix_bedrock_tasks_parent_sort" not in indexes:
        op.create_index("ix_bedrock_tasks_parent_sort", "bedrock_tasks", ["parent_id", "sort_order"])

    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("user_notifications"):
        op.create_table(
            "user_notifications",
            sa.Column("id", sa.String(length=20), primary_key=True),
            sa.Column("user_id", sa.String(length=20), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("kind", sa.String(length=40), nullable=False, server_default="task_turn"),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("body", sa.Text(), nullable=True),
            sa.Column("resource_key", sa.String(length=80), nullable=True),
            sa.Column("resource_id", sa.String(length=40), nullable=True),
            sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_user_notifications_user_id", "user_notifications", ["user_id"])
        op.create_index("ix_user_notifications_resource_id", "user_notifications", ["resource_id"])
        op.create_index(
            "ix_user_notifications_unread",
            "user_notifications",
            ["user_id", "read_at", "created_at"],
        )
    op.execute(sa.text("CREATE SEQUENCE IF NOT EXISTS ntf_id_seq START 1"))


def downgrade() -> None:
    op.drop_index("ix_user_notifications_unread", table_name="user_notifications")
    op.drop_index("ix_user_notifications_resource_id", table_name="user_notifications")
    op.drop_index("ix_user_notifications_user_id", table_name="user_notifications")
    op.drop_table("user_notifications")
    op.execute(sa.text("DROP SEQUENCE IF EXISTS ntf_id_seq"))

    op.drop_index("ix_bedrock_tasks_parent_sort", table_name="bedrock_tasks")
    op.drop_index("ix_bedrock_tasks_parent_id", table_name="bedrock_tasks")
    op.drop_constraint("fk_bedrock_tasks_parent_id", "bedrock_tasks", type_="foreignkey")
    op.drop_column("bedrock_tasks", "turn_notified_at")
    op.drop_column("bedrock_tasks", "execute_on_turn")
    op.drop_column("bedrock_tasks", "is_blocking")
    op.drop_column("bedrock_tasks", "sort_order")
    op.drop_column("bedrock_tasks", "parent_id")
