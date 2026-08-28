"""Re-key admin_section_overrides al PK sintético ``sec-N`` (ADR-021).

Antes, ``admin_section_overrides.section_id`` guardaba el slug legible
(``dashboard``, ``career-projects``, ``settings-error-reports``…). Ese valor pasa
a ser ``AdminSectionSpec.system_name`` y la clave canónica de la sección es ahora
el PK sintético ``sec-N`` (prefijo ``sec-``, análogo a ``err-N``).

Esta migración traduce las filas existentes con un **mapa estático incrustado**
(slug -> sec-N); NO importa ``services.admin_sections`` para no acoplar el
historial de migraciones al código de la app. Filas cuyo ``section_id`` no está
en el mapa (ni es ya un ``sec-N`` conocido) se dejan intactas y se registran en
el log — un override huérfano no rompe nada (el catálogo lo ignora).

Nota de deploy (igual que la migración b1c2d3e4f5a6 / ADR-019): esto NO corre en
``init_db`` (que usa ``create_all``). Tras el rebuild hay que ejecutar
``alembic upgrade head``.

Revision ID: b2c3d4e5f6a7
Revises: b1c2d3e4f5a6
Create Date: 2026-08-27
"""
import logging
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, tuple, None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "admin_section_overrides"
_log = logging.getLogger("alembic.runtime.migration")

# Mapa CONGELADO slug (antiguo section_id / nuevo system_name) -> PK sec-N.
# Debe coincidir con services/admin_sections.py. No se reordena ni se reutiliza.
_SLUG_TO_PK: dict[str, str] = {
    "dashboard": "sec-1",
    "metrics": "sec-2",
    "search-metrics": "sec-3",
    "agent-metrics": "sec-4",
    "files": "sec-5",
    "linkedin-publish": "sec-6",
    "job-discovery": "sec-7",
    "pdf-templates": "sec-8",
    "pdf-styles": "sec-9",
    "agent-tasks": "sec-10",
    "agent-chat": "sec-11",
    "agent-memory": "sec-12",
    "agent-instructions": "sec-13",
    "agent-tools": "sec-14",
    "agent-audit-log": "sec-15",
    "settings-agents": "sec-16",
    "settings-sections": "sec-17",
    "settings-agent-prompts": "sec-18",
    "settings-error-reports": "sec-19",
    "career-personal-profile": "sec-20",
    "career-differentiators": "sec-21",
    "career-identity": "sec-22",
    "career-identity-reflections": "sec-23",
    "career-competencies": "sec-24",
    "career-certifications": "sec-25",
    "career-target-roles": "sec-26",
    "career-work-history": "sec-27",
    "career-achievements": "sec-28",
    "career-star-stories": "sec-29",
    "career-career-reviews": "sec-30",
    "career-role-gap-analysis": "sec-31",
    "career-projects": "sec-32",
    "career-fit-scoring-factors": "sec-33",
    "career-market-segments": "sec-34",
    "career-role-narratives": "sec-35",
    "career-search-plans": "sec-36",
    "career-networking-contacts": "sec-37",
    "career-target-companies": "sec-38",
    "career-vacancies": "sec-39",
    "career-cv-versions": "sec-40",
    "career-cover-letter-versions": "sec-41",
    "career-applications": "sec-42",
    "career-application-interactions": "sec-43",
    "career-interviews": "sec-44",
    "career-linkedin-profile": "sec-45",
    "career-github-profile": "sec-46",
    "career-portal-home": "sec-47",
    "career-portal-about": "sec-48",
    "career-portal-contact": "sec-49",
    "career-publications": "sec-50",
    "career-contact-interactions": "sec-51",
    "career-networking-activities": "sec-52",
    "career-tags": "sec-53",
    "career-operational-methodologies": "sec-54",
}


def _rekey(pairs: Sequence[tuple[str, str]], *, known_targets: set[str]) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table(_TABLE):
        return

    existing = {
        r[0]
        for r in bind.execute(sa.text(f"SELECT section_id FROM {_TABLE}")).fetchall()
    }
    unmatched = existing - {old for old, _ in pairs} - known_targets
    if unmatched:
        _log.warning(
            "%s: %d fila(s) con section_id sin mapa, se dejan intactas: %s",
            _TABLE,
            len(unmatched),
            sorted(unmatched),
        )

    for old, new in pairs:
        if old not in existing:
            continue
        bind.execute(
            sa.text(
                f"UPDATE {_TABLE} SET section_id = :new WHERE section_id = :old"
            ),
            {"new": new, "old": old},
        )


def upgrade() -> None:
    pairs = list(_SLUG_TO_PK.items())
    _rekey(pairs, known_targets=set(_SLUG_TO_PK.values()))
    op.alter_column(
        _TABLE,
        "section_id",
        type_=sa.String(40),
        existing_type=sa.String(80),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        _TABLE,
        "section_id",
        type_=sa.String(80),
        existing_type=sa.String(40),
        existing_nullable=False,
    )
    pairs = [(pk, slug) for slug, pk in _SLUG_TO_PK.items()]
    _rekey(pairs, known_targets=set(_SLUG_TO_PK.keys()))
