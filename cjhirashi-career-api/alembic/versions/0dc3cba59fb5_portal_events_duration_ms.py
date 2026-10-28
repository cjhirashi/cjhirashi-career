"""Add portal_events.duration_ms, captured as a separate 'page_duration'
event (sendBeacon, fired on route change/tab close) - how long a visitor
actually stayed on a page, not just whether they viewed it.

Revision ID: 0dc3cba59fb5
Revises: 058d4b7020d5
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0dc3cba59fb5"
down_revision: Union[str, None] = "058d4b7020d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "portal_events"


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns(_TABLE)}
    if "duration_ms" not in columns:
        op.add_column(_TABLE, sa.Column("duration_ms", sa.Integer(), nullable=True))


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns(_TABLE)}
    if "duration_ms" in columns:
        op.drop_column(_TABLE, "duration_ms")
