"""Retira ``admin_section_overrides.description`` (feature 001).

El override editable de "descripción de sección" se elimina: su propósito lo
cubren ahora las instrucciones del sidebar derecho (``views[view].sidebar_body``,
renderizadas como Markdown). El registro de código sigue teniendo la descripción
de cada sección para el catálogo; sólo desaparece la columna de override en PG.

La migración es DDL puro: `drop_column` en ``upgrade`` y su inversa en
``downgrade``. NO toca ``views`` ni ``agent_profile_id`` de ninguna fila.

Nota de deploy (igual que b1c2d3e4f5a6 / ADR-019): esto NO corre en ``init_db``
(que usa ``create_all``). Tras el rebuild hay que ejecutar ``alembic upgrade head``.

Revision ID: c4d5e6f7a8b9
Revises: b2c3d4e5f6a7
Create Date: 2026-09-04
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "admin_section_overrides"
_COLUMN = "description"


def upgrade() -> None:
    op.drop_column(_TABLE, _COLUMN)


def downgrade() -> None:
    op.add_column(_TABLE, sa.Column(_COLUMN, sa.Text(), nullable=True))
