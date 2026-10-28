"""search_platforms table (job search platforms + profile loaded on each) +
vacancies.search_platform_id FK.

Revision ID: 8d756b313e88
Revises: ca4ad88923c6
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "8d756b313e88"
down_revision: Union[str, None] = "ca4ad88923c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SEQUENCE IF NOT EXISTS spf_id_seq START 1")

    op.create_table(
        "search_platforms",
        sa.Column("id", sa.String(length=20), nullable=False),
        sa.Column("user_id", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("profile_url", sa.String(length=500), nullable=True),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("profile_headline", sa.String(length=500), nullable=True),
        sa.Column("profile_notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.text("true")),
        sa.Column("last_updated_at", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_search_platforms_user_id", "search_platforms", ["user_id"])

    op.add_column("vacancies", sa.Column("search_platform_id", sa.String(length=20), nullable=True))
    op.create_foreign_key(
        "fk_vacancies_search_platform_id",
        "vacancies",
        "search_platforms",
        ["search_platform_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_vacancies_search_platform_id", "vacancies", ["search_platform_id"])


def downgrade() -> None:
    op.drop_index("ix_vacancies_search_platform_id", table_name="vacancies")
    op.drop_constraint("fk_vacancies_search_platform_id", "vacancies", type_="foreignkey")
    op.drop_column("vacancies", "search_platform_id")

    op.drop_index("ix_search_platforms_user_id", table_name="search_platforms")
    op.drop_table("search_platforms")
    op.execute("DROP SEQUENCE IF EXISTS spf_id_seq")
