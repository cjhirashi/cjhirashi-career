"""Add portal_events.latitude/longitude (feeds the bubble map in Métricas).

Revision ID: 4e710815fede
Revises: 5ff0c9b8b078
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "4e710815fede"
down_revision: Union[str, None] = "5ff0c9b8b078"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "portal_events"


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns(_TABLE)}
    if "latitude" not in columns:
        op.add_column(_TABLE, sa.Column("latitude", sa.Float(), nullable=True))
    if "longitude" not in columns:
        op.add_column(_TABLE, sa.Column("longitude", sa.Float(), nullable=True))


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns(_TABLE)}
    if "longitude" in columns:
        op.drop_column(_TABLE, "longitude")
    if "latitude" in columns:
        op.drop_column(_TABLE, "latitude")
