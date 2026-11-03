"""Drop linkedin_posts and linkedin_connections: the LinkedIn publishing
integration (OAuth, post queue, scheduler) was removed; the portfolio blog
(publications) is the only publishing surface.

Revision ID: a7c1e9d2f4b8
Revises: 0dc3cba59fb5
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a7c1e9d2f4b8"
down_revision: Union[str, None] = "0dc3cba59fb5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    for table in ("linkedin_posts", "linkedin_connections"):
        if table in tables:
            op.drop_table(table)
    # Mirror row of the retired "LinkedIn · Publicar" section (cascades to its views).
    if "admin_sections_l1" in tables:
        op.execute("DELETE FROM admin_sections_l1 WHERE system_name = 'linkedin-publish'")


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "linkedin_connections" not in tables:
        op.create_table(
            "linkedin_connections",
            sa.Column("id", sa.String(20), primary_key=True),
            sa.Column("user_id", sa.String(20), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("access_token", sa.String(2048), nullable=False),
            sa.Column("member_sub", sa.String(255), nullable=False),
            sa.Column("member_name", sa.String(255), nullable=True),
            sa.Column("member_email", sa.String(255), nullable=True),
            sa.Column("profile_picture_url", sa.String(1024), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("connected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("user_id"),
        )
        op.create_index("ix_linkedin_connections_id", "linkedin_connections", ["id"])
        op.create_index("ix_linkedin_connections_user_id", "linkedin_connections", ["user_id"])
    if "linkedin_posts" not in tables:
        op.create_table(
            "linkedin_posts",
            sa.Column("id", sa.String(20), primary_key=True),
            sa.Column("user_id", sa.String(20), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("text", sa.Text(), nullable=False),
            sa.Column("image_url", sa.String(1024), nullable=True),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("linkedin_post_urn", sa.String(255), nullable=True),
            sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_linkedin_posts_id", "linkedin_posts", ["id"])
        op.create_index("ix_linkedin_posts_user_id", "linkedin_posts", ["user_id"])
