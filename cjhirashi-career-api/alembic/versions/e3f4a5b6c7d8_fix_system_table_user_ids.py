"""Fix user_id type on system/telemetry tables after prefixed users.id migration.

Revision ID: e3f4a5b6c7d8
Revises: d1e2f3a4b5c6
Create Date: 2026-08-24

These tables were missed by d1e2f3a4b5c6 and still had INTEGER user_id while
users.id became VARCHAR(usr-N). That breaks Bedrock budget checks and audit queries.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e3f4a5b6c7d8"
down_revision: Union[str, None] = "d1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = (
    "bedrock_usage_logs",
    "bedrock_usage_round_logs",
    "audit_logs",
    "events",
    "metrics",
)


def upgrade() -> None:
    conn = op.get_bind()
    for table in _TABLES:
        conn.execute(
            sa.text(
                f"ALTER TABLE {table} ALTER COLUMN user_id TYPE VARCHAR(20) "
                f"USING 'usr-' || user_id::text"
            )
        )
        conn.execute(
            sa.text(
                f"ALTER TABLE {table} ADD CONSTRAINT {table}_user_id_fkey "
                f"FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE"
            )
        )


def downgrade() -> None:
    conn = op.get_bind()
    for table in reversed(_TABLES):
        conn.execute(sa.text(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {table}_user_id_fkey"))
        conn.execute(
            sa.text(
                f"ALTER TABLE {table} ALTER COLUMN user_id TYPE INTEGER "
                f"USING NULLIF(regexp_replace(user_id, '^usr-', ''), '')::integer"
            )
        )
