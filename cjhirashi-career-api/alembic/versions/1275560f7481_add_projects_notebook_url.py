"""Add projects.notebook_url (companion to github_url/demo_url).

Revision ID: 1275560f7481
Revises: d8f2b5a13c97
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "1275560f7481"
down_revision: Union[str, None] = "d8f2b5a13c97"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "projects"


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns(_TABLE)}
    if "notebook_url" not in columns:
        op.add_column(_TABLE, sa.Column("notebook_url", sa.String(length=500), nullable=True))


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns(_TABLE)}
    if "notebook_url" in columns:
        op.drop_column(_TABLE, "notebook_url")
