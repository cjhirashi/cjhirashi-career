"""Add explicit authorization class to users.

Revision ID: f8a9b0c1d2e3
Revises: f7a8b9c0d1e2
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f8a9b0c1d2e3"
down_revision: Union[str, None] = "c5d6e7f8a9b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("users")}
    if "access_role" not in columns:
        op.add_column(
            "users",
            sa.Column("access_role", sa.String(length=32), nullable=False, server_default="user"),
        )
        op.create_index("ix_users_access_role", "users", ["access_role"], unique=False)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    indexes = {index["name"] for index in inspector.get_indexes("users")}
    if "ix_users_access_role" in indexes:
        op.drop_index("ix_users_access_role", table_name="users")
    columns = {column["name"] for column in inspector.get_columns("users")}
    if "access_role" in columns:
        op.drop_column("users", "access_role")
