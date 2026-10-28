"""Link cv_versions to the vacancy it was actually sent for (vacancies.cv_version_id)
and to the platform it was uploaded to at registration (search_platforms.cv_version_id).

Revision ID: fa5fb4f6d183
Revises: d017df3fa6c5
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "fa5fb4f6d183"
down_revision: Union[str, None] = "d017df3fa6c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("vacancies", sa.Column("cv_version_id", sa.String(length=20), nullable=True))
    op.create_foreign_key(
        "fk_vacancies_cv_version_id",
        "vacancies",
        "cv_versions",
        ["cv_version_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_vacancies_cv_version_id", "vacancies", ["cv_version_id"])

    op.add_column("search_platforms", sa.Column("cv_version_id", sa.String(length=20), nullable=True))
    op.create_foreign_key(
        "fk_search_platforms_cv_version_id",
        "search_platforms",
        "cv_versions",
        ["cv_version_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_search_platforms_cv_version_id", "search_platforms", ["cv_version_id"])


def downgrade() -> None:
    op.drop_index("ix_search_platforms_cv_version_id", table_name="search_platforms")
    op.drop_constraint("fk_search_platforms_cv_version_id", "search_platforms", type_="foreignkey")
    op.drop_column("search_platforms", "cv_version_id")

    op.drop_index("ix_vacancies_cv_version_id", table_name="vacancies")
    op.drop_constraint("fk_vacancies_cv_version_id", "vacancies", type_="foreignkey")
    op.drop_column("vacancies", "cv_version_id")
