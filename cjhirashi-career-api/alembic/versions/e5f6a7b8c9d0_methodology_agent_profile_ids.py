"""Add agent_profile_ids to operational_methodologies.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-25
"""
import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Backfill por `section` alineado con methodology_sections de los perfiles.
_SECTION_AGENTS = {
    "Identidad Profesional": ["agent_professional_identity"],
    "Operativa de Búsqueda": [
        "agent_search_operations",
        "agent_vacancy_search",
        "agent_cv_writing",
        "agent_cover_letter_writing",
    ],
    "Presencia Digital": [
        "agent_digital_presence",
        "agent_linkedin_publishing",
        "agent_github",
    ],
    "Networking": ["agent_networking"],
    "Soporte": ["agent_support"],
    "Diseño PDF": ["agent_pdf_design", "agent_pdf_render"],
    "Diseño Visual": ["agent_visual_design"],
    "Infraestructura Técnica": ["agent_pdf_design", "agent_pdf_render"],
}


def upgrade() -> None:
    op.add_column(
        "operational_methodologies",
        sa.Column("agent_profile_ids", JSONB(), nullable=True),
    )
    conn = op.get_bind()
    for section, ids in _SECTION_AGENTS.items():
        conn.execute(
            sa.text(
                """
                UPDATE operational_methodologies
                SET agent_profile_ids = CAST(:ids AS jsonb)
                WHERE section = :section
                  AND agent_profile_ids IS NULL
                """
            ),
            {"ids": json.dumps(ids), "section": section},
        )


def downgrade() -> None:
    op.drop_column("operational_methodologies", "agent_profile_ids")
