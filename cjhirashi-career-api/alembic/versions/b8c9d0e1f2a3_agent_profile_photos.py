"""Agent catalog photos from the MinIO bucket.

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-08-26
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b8c9d0e1f2a3"
down_revision: Union[str, tuple, None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table("bedrock_agent_profile_photos"):
        return
    op.create_table(
        "bedrock_agent_profile_photos",
        sa.Column("profile_id", sa.String(length=50), primary_key=True),
        sa.Column("photo_url", sa.String(length=1024), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table("bedrock_agent_profile_photos"):
        op.drop_table("bedrock_agent_profile_photos")
