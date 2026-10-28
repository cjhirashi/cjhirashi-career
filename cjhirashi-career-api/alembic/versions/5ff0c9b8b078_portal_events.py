"""portal_events table - anonymous portfolio traffic (pageview/click/download)
captured by POST /events/track, with country/region/city resolved server-side.

Revision ID: 5ff0c9b8b078
Revises: fa5fb4f6d183
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "5ff0c9b8b078"
down_revision: Union[str, None] = "fa5fb4f6d183"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SEQUENCE IF NOT EXISTS pev_id_seq START 1")

    op.create_table(
        "portal_events",
        sa.Column("id", sa.String(length=20), nullable=False),
        sa.Column("user_id", sa.String(length=20), nullable=False),
        sa.Column("event_type", sa.String(length=30), nullable=False),
        sa.Column("page", sa.String(length=500), nullable=False),
        sa.Column("target", sa.String(length=255), nullable=True),
        sa.Column("event_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("region", sa.String(length=100), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_portal_events_user_id", "portal_events", ["user_id"])
    op.create_index("ix_portal_events_event_type", "portal_events", ["event_type"])
    op.create_index("ix_portal_events_page", "portal_events", ["page"])
    op.create_index("ix_portal_events_country", "portal_events", ["country"])
    op.create_index("ix_portal_events_created_at", "portal_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_portal_events_created_at", table_name="portal_events")
    op.drop_index("ix_portal_events_country", table_name="portal_events")
    op.drop_index("ix_portal_events_page", table_name="portal_events")
    op.drop_index("ix_portal_events_event_type", table_name="portal_events")
    op.drop_index("ix_portal_events_user_id", table_name="portal_events")
    op.drop_table("portal_events")
    op.execute("DROP SEQUENCE IF EXISTS pev_id_seq")
