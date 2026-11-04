"""Add contact_messages table for portfolio contact form submissions.

Revision ID: 4439c6915701
Revises: b8d2f4a6c1e9
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "4439c6915701"
down_revision: Union[str, None] = "b8d2f4a6c1e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create contact_messages table
    op.create_table(
        "contact_messages",
        sa.Column("id", sa.String(length=20), nullable=False),
        sa.Column("user_id", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="new"),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('new', 'read', 'archived')", name="ck_contact_message_status"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    # Create indexes
    op.create_index("ix_contact_messages_user_id", "contact_messages", ["user_id"])
    op.create_index("ix_contact_messages_status", "contact_messages", ["status"])
    op.create_index("ix_contact_messages_created_at", "contact_messages", ["created_at"])
    op.create_index(
        "ix_contact_messages_user_status_created",
        "contact_messages",
        ["user_id", "status", "created_at"],
    )

    # Create sequence for ID generation
    op.execute("CREATE SEQUENCE IF NOT EXISTS cmg_id_seq START 1")


def downgrade() -> None:
    # Drop sequence
    op.execute("DROP SEQUENCE IF EXISTS cmg_id_seq")
    # Drop indexes
    op.drop_index("ix_contact_messages_user_status_created", table_name="contact_messages")
    op.drop_index("ix_contact_messages_created_at", table_name="contact_messages")
    op.drop_index("ix_contact_messages_status", table_name="contact_messages")
    op.drop_index("ix_contact_messages_user_id", table_name="contact_messages")
    # Drop table
    op.drop_table("contact_messages")
