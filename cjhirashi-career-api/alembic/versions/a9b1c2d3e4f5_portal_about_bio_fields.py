"""Add portal_about.headline, bio_text, timeline_milestones (checklist Paulina #12).

photo_url + name alone are insufficient for a public "About me" page.

Revision ID: a9b1c2d3e4f5
Revises: f8a9b1c2d3e4
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a9b1c2d3e4f5"
down_revision: Union[str, None] = "f8a9b1c2d3e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "portal_about"
_NEW_COLUMNS = [
    ("headline", sa.String(length=255)),
    ("bio_text", sa.Text()),
    ("timeline_milestones", postgresql.JSONB()),
]


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns(_TABLE)}
    for name, col_type in _NEW_COLUMNS:
        if name not in columns:
            op.add_column(_TABLE, sa.Column(name, col_type, nullable=True))


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns(_TABLE)}
    for name, _ in reversed(_NEW_COLUMNS):
        if name in columns:
            op.drop_column(_TABLE, name)
