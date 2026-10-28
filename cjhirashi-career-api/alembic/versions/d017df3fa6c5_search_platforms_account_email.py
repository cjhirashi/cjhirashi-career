"""Add search_platforms.account_email (which inbox to watch per platform).

Revision ID: d017df3fa6c5
Revises: 8d756b313e88
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d017df3fa6c5"
down_revision: Union[str, None] = "8d756b313e88"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "search_platforms"


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns(_TABLE)}
    if "account_email" not in columns:
        op.add_column(_TABLE, sa.Column("account_email", sa.String(length=255), nullable=True))


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns(_TABLE)}
    if "account_email" in columns:
        op.drop_column(_TABLE, "account_email")
