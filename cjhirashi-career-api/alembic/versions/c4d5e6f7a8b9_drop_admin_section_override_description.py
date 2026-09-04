"""Retira ``admin_section_overrides.description`` (feature 001).

El override editable de "descripción de sección" se elimina: su propósito lo
cubren ahora las instrucciones del sidebar derecho (``views[view].sidebar_body``,
renderizadas como Markdown). El registro de código sigue teniendo la descripción
de cada sección para el catálogo; sólo desaparece la columna de override en PG.

La migración es DDL puro e **idempotente** (``DROP COLUMN IF EXISTS`` /
``ADD COLUMN IF NOT EXISTS``, mismo patrón que d1e2f3a4b5c6): en un entorno nuevo
``init_db`` corre ``create_all`` con los modelos actuales — que ya NO tienen
``description`` — así que la columna puede no existir cuando se ejecute esto.
NO toca ``views`` ni ``agent_profile_id`` de ninguna fila.

Nota de deploy: esto NO corre en ``init_db``. Tras el rebuild hay que ejecutar
``alembic upgrade head``.

Revision ID: c4d5e6f7a8b9
Revises: b2c3d4e5f6a7
Create Date: 2026-09-04
"""
from typing import Sequence, Union

from alembic import op

revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "admin_section_overrides"
_COLUMN = "description"


def upgrade() -> None:
    op.execute(f'ALTER TABLE {_TABLE} DROP COLUMN IF EXISTS {_COLUMN}')


def downgrade() -> None:
    op.execute(f'ALTER TABLE {_TABLE} ADD COLUMN IF NOT EXISTS {_COLUMN} TEXT')
