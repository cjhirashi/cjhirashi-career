"""Tokens de prompt caching de Bedrock en los logs de uso.

Añade cache_read_tokens / cache_write_tokens a bedrock_usage_logs y
bedrock_usage_round_logs para que el panel de costos distinga la entrada
normal de la lectura/escritura de caché (0.10x / 1.25x del precio de entrada).

Revision ID: b1c2d3e4f5a6
Revises: a9b8c7d6e5f4
Create Date: 2026-08-27
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, tuple, None] = "a9b8c7d6e5f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = ("bedrock_usage_logs", "bedrock_usage_round_logs")
_COLUMNS = ("cache_read_tokens", "cache_write_tokens")


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    for table in _TABLES:
        if not inspector.has_table(table):
            continue
        existing = {c["name"] for c in inspector.get_columns(table)}
        for column in _COLUMNS:
            if column not in existing:
                op.add_column(
                    table,
                    sa.Column(column, sa.Integer(), nullable=False, server_default="0"),
                )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    for table in _TABLES:
        if not inspector.has_table(table):
            continue
        existing = {c["name"] for c in inspector.get_columns(table)}
        for column in _COLUMNS:
            if column in existing:
                op.drop_column(table, column)
