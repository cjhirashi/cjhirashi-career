"""Add global_rules override column to bedrock_settings.

Same override pattern as `system_prompt`: NULL/empty means "use the
built-in default" (see services/bedrock/prompt.py::default_global_rules).
Carries the rules that apply to every agent regardless of level/profile
(grounding + methodology assignment), previously hardcoded only in code.

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-08-26
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, tuple, None] = "b8c9d0e1f2a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    columns = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("bedrock_settings")}
    if "global_rules" not in columns:
        op.add_column("bedrock_settings", sa.Column("global_rules", sa.Text(), nullable=True))


def downgrade() -> None:
    columns = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("bedrock_settings")}
    if "global_rules" in columns:
        op.drop_column("bedrock_settings", "global_rules")
