"""Add target_companies research fields (checklist Paulina #10).

industry_sector, company_culture, funding_stage, tech_stack,
company_website, linkedin_company_url, hiring_velocity,
last_researched_at, review_score. funding_stage and tech_stack feed the
"Prestige/Brand" and "Technology Stack" factors in fit_scoring_factors,
which today have no data source.

Revision ID: e7f8a9b1c2d3
Revises: d6e7f8a9b1c2
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e7f8a9b1c2d3"
down_revision: Union[str, None] = "d6e7f8a9b1c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "target_companies"
_NEW_COLUMNS = [
    ("industry_sector", sa.String(length=100)),
    ("company_culture", sa.Text()),
    ("funding_stage", sa.String(length=50)),
    ("tech_stack", postgresql.JSONB()),
    ("company_website", sa.String(length=500)),
    ("linkedin_company_url", sa.String(length=500)),
    ("hiring_velocity", sa.String(length=30)),
    ("last_researched_at", sa.Date()),
    ("review_score", sa.Float()),
]


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns(_TABLE)}
    for name, col_type in _NEW_COLUMNS:
        if name not in columns:
            op.add_column(_TABLE, sa.Column(name, col_type, nullable=True))


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns(_TABLE)}
    for name, _ in reversed(_NEW_COLUMNS):
        if name in columns:
            op.drop_column(_TABLE, name)
