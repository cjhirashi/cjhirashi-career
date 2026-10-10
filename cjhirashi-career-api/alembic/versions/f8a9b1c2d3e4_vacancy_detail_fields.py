"""Add vacancies detail fields + contact_id FK (checklist Paulina #11).

location, work_modality, seniority_level, salary_min, salary_max,
required_skills, years_experience_required, posted_date,
application_status, priority, contracting_model, contact_id (FK to
networking_contacts, SET NULL on delete).

Revision ID: f8a9b1c2d3e4
Revises: e7f8a9b1c2d3
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f8a9b1c2d3e4"
down_revision: Union[str, None] = "e7f8a9b1c2d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "vacancies"
_FK_NAME = "fk_vacancies_contact_id_networking_contacts"
_NEW_COLUMNS = [
    ("location", sa.String(length=255)),
    ("work_modality", sa.String(length=100)),
    ("seniority_level", sa.String(length=50)),
    ("salary_min", sa.Integer()),
    ("salary_max", sa.Integer()),
    ("required_skills", postgresql.JSONB()),
    ("years_experience_required", sa.Integer()),
    ("posted_date", sa.Date()),
    ("application_status", sa.String(length=30)),
    ("priority", sa.String(length=10)),
    ("contracting_model", sa.String(length=50)),
    ("contact_id", sa.String(length=20)),
]


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns(_TABLE)}
    for name, col_type in _NEW_COLUMNS:
        if name not in columns:
            op.add_column(_TABLE, sa.Column(name, col_type, nullable=True))

    fks = {fk["name"] for fk in inspector.get_foreign_keys(_TABLE)}
    if _FK_NAME not in fks:
        op.create_foreign_key(
            _FK_NAME,
            _TABLE,
            "networking_contacts",
            ["contact_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    fks = {fk["name"] for fk in inspector.get_foreign_keys(_TABLE)}
    if _FK_NAME in fks:
        op.drop_constraint(_FK_NAME, _TABLE, type_="foreignkey")

    columns = {column["name"] for column in inspector.get_columns(_TABLE)}
    for name, _ in reversed(_NEW_COLUMNS):
        if name in columns:
            op.drop_column(_TABLE, name)
