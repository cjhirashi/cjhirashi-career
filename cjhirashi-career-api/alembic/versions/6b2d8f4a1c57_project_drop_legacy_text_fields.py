"""Projects: retira los campos de texto anteriores (ADR-030).

Su contenido ya vive en presentacion, tecnico y estado.
El downgrade recrea las columnas vacías; los datos se recuperan del respaldo previo.

Revision ID: 6b2d8f4a1c57
Revises: 5a1c7e9d2b30
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "6b2d8f4a1c57"
down_revision: Union[str, None] = "5a1c7e9d2b30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TEXT = ["detailed_summary", "problem", "solution", "architecture", "approach_steps", "repo_structure"]


def upgrade() -> None:
    for name in _TEXT:
        op.drop_column("projects", name)
    op.drop_column("projects", "results")


def downgrade() -> None:
    op.add_column("projects", sa.Column("results", JSONB(), nullable=True))
    for name in reversed(_TEXT):
        op.add_column("projects", sa.Column(name, sa.Text(), nullable=True))
