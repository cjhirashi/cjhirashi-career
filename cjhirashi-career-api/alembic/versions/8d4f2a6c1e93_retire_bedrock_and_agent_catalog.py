"""Retira el subsistema Bedrock: tablas del harness, del catálogo de agentes y de las secciones del Admin.

Conserva `bedrock_tasks` (tablero de tareas) y `audit_logs`. Quita de `operational_methodologies` las columnas
`agent_profile_ids` y `section_ids` (asignación a agentes y secciones). No tiene vuelta atrás automática:
los datos se recuperan del respaldo previo (pg_dump de las tablas `bedrock_*`, `admin_section_overrides`).

Revision ID: 8d4f2a6c1e93
Revises: 7c3e1d9a5b82
"""
from typing import Sequence, Union

from alembic import op

revision: str = "8d4f2a6c1e93"
down_revision: Union[str, None] = "7c3e1d9a5b82"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = [
    "bedrock_conversation_messages",
    "bedrock_conversations",
    "bedrock_usage_round_logs",
    "bedrock_usage_logs",
    "bedrock_agent_profile_tools",
    "bedrock_agent_profile_prompts",
    "bedrock_agent_profile_photos",
    "bedrock_agent_delegation",
    "bedrock_custom_tools",
    "bedrock_settings",
    "admin_section_overrides",
]


def upgrade() -> None:
    for name in _TABLES:
        op.execute(f"DROP TABLE IF EXISTS {name} CASCADE")
    op.execute("ALTER TABLE operational_methodologies DROP COLUMN IF EXISTS agent_profile_ids")
    op.execute("ALTER TABLE operational_methodologies DROP COLUMN IF EXISTS section_ids")


def downgrade() -> None:
    raise NotImplementedError("Retiro de Bedrock: restaurar desde el respaldo (pg_dump) previo a esta migración.")
