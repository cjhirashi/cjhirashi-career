"""Add portal_events.session_id (groups pageviews from the same browser
session into one visit, instead of counting every pageview as a visit).

Revision ID: 058d4b7020d5
Revises: 4e710815fede
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "058d4b7020d5"
down_revision: Union[str, None] = "4e710815fede"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "portal_events"


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns(_TABLE)}
    if "session_id" not in columns:
        op.add_column(_TABLE, sa.Column("session_id", sa.String(length=64), nullable=True))
        op.create_index("ix_portal_events_session_id", _TABLE, ["session_id"])


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns(_TABLE)}
    if "session_id" in columns:
        op.drop_index("ix_portal_events_session_id", table_name=_TABLE)
        op.drop_column(_TABLE, "session_id")
