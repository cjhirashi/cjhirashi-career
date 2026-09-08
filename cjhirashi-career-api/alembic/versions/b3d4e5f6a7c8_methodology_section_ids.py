"""operational_methodologies.section_ids + limpiar ids L2 de agent_profile_ids

Spec 004: los agentes L2 reciben herramientas y metodologías vía sus secciones;
`agent_profile_ids` queda sólo para L1/L3. Esta migración añade `section_ids` y
retira los ids de nivel 2 de `agent_profile_ids` (el operador re-liga las
metodologías a secciones desde /settings/sections/:id).

Revision ID: b3d4e5f6a7c8
Revises: f7a8b9c0d1e2
"""
import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b3d4e5f6a7c8"
down_revision: Union[str, None] = "f7a8b9c0d1e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    # 1. Columna nueva, idempotente.
    op.execute(
        "ALTER TABLE operational_methodologies ADD COLUMN IF NOT EXISTS section_ids JSONB"
    )

    # 2. Retirar los ids de nivel 2 de agent_profile_ids (idempotente: re-correr
    #    no encuentra ninguno). El set de ids L2 se toma del catálogo en código.
    from services.bedrock.agent_profiles import list_profiles

    l2_ids = sorted(p.id for p in list_profiles() if p.level == 2)
    if not l2_ids:
        return

    rows = bind.execute(
        sa.text(
            "SELECT id, agent_profile_ids FROM operational_methodologies "
            "WHERE agent_profile_ids IS NOT NULL"
        )
    ).fetchall()
    l2_set = set(l2_ids)
    for row_id, ids in rows:
        if not isinstance(ids, list):
            continue
        kept = [x for x in ids if x not in l2_set]
        if kept != ids:
            bind.execute(
                sa.text(
                    "UPDATE operational_methodologies "
                    "SET agent_profile_ids = CAST(:v AS JSONB) WHERE id = :id"
                ),
                {"v": json.dumps(kept), "id": row_id},
            )


def downgrade() -> None:
    # No restaura los ids L2 retirados (no se guardó el estado previo).
    op.execute(
        "ALTER TABLE operational_methodologies DROP COLUMN IF EXISTS section_ids"
    )
