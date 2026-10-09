"""Add vacancies.target_company_id FK to target_companies (checklist Paulina #6).

`vacancies.company` stays free text (vacancies at companies outside the
target-companies list are still tracked), but when a vacancy does belong to
an already-researched target company, this FK lets the app cross data
between both tables reliably instead of matching on free-text company names.

Revision ID: a2b3c4d5e6f7
Revises: f8a9b0c1d2e3
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a2b3c4d5e6f7"
down_revision: Union[str, None] = "f8a9b0c1d2e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "vacancies"
_COLUMN = "target_company_id"
_FK_NAME = "fk_vacancies_target_company_id_target_companies"
_IX_NAME = "ix_vacancies_target_company_id"


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns(_TABLE)}
    if _COLUMN not in columns:
        op.add_column(_TABLE, sa.Column(_COLUMN, sa.String(length=20), nullable=True))

    indexes = {index["name"] for index in inspector.get_indexes(_TABLE)}
    if _IX_NAME not in indexes:
        op.create_index(_IX_NAME, _TABLE, [_COLUMN], unique=False)

    fks = {fk["name"] for fk in inspector.get_foreign_keys(_TABLE)}
    if _FK_NAME not in fks:
        op.create_foreign_key(
            _FK_NAME,
            _TABLE,
            "target_companies",
            [_COLUMN],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    fks = {fk["name"] for fk in inspector.get_foreign_keys(_TABLE)}
    if _FK_NAME in fks:
        op.drop_constraint(_FK_NAME, _TABLE, type_="foreignkey")

    indexes = {index["name"] for index in inspector.get_indexes(_TABLE)}
    if _IX_NAME in indexes:
        op.drop_index(_IX_NAME, table_name=_TABLE)

    columns = {column["name"] for column in inspector.get_columns(_TABLE)}
    if _COLUMN in columns:
        op.drop_column(_TABLE, _COLUMN)
