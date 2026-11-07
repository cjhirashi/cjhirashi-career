"""Projects: 3 campos markdown (presentacion, tecnico, estado) + estado_verificado_el.

Aditiva: no toca ni elimina los campos anteriores.

Revision ID: 5a1c7e9d2b30
Revises: 4439c6915701
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "5a1c7e9d2b30"
down_revision: Union[str, None] = "4439c6915701"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("presentacion", sa.Text(), nullable=True))
    op.add_column("projects", sa.Column("tecnico", sa.Text(), nullable=True))
    op.add_column("projects", sa.Column("estado", sa.Text(), nullable=True))
    op.add_column("projects", sa.Column("estado_verificado_el", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "estado_verificado_el")
    op.drop_column("projects", "estado")
    op.drop_column("projects", "tecnico")
    op.drop_column("projects", "presentacion")
