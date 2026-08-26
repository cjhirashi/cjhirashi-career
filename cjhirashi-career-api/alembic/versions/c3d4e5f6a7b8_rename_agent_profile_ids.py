"""Rename Bedrock agent profile ids to agent_<name>.

L1/L2: English label (agent_orchestrator, agent_professional_identity, …).
L3: previous id with prefix (agent_pdf_render, agent_changelog, …).

Revision ID: c3d4e5f6a7b8
Revises: a8b9c0d1e2f3
Create Date: 2026-08-25
"""
from typing import Sequence, Union

from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "a8b9c0d1e2f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_RENAMES = (
    ("orchestrator", "agent_orchestrator"),
    ("identity", "agent_professional_identity"),
    ("search", "agent_search_operations"),
    ("digital", "agent_digital_presence"),
    ("networking", "agent_networking"),
    ("support", "agent_support"),
    ("methodologies", "agent_methodologies"),
    ("pdf_design", "agent_pdf_design"),
    ("pdf_render", "agent_pdf_render"),
    ("visual_design", "agent_visual_design"),
    ("changelog", "agent_changelog"),
    ("task_manager", "agent_task_manager"),
)

_COLUMNS = (
    ("bedrock_conversations", "agent_profile_id"),
    ("bedrock_usage_round_logs", "agent_profile_id"),
)


def _rewrite(pairs: Sequence[tuple[str, str]]) -> None:
    for table, column in _COLUMNS:
        for old, new in pairs:
            op.execute(
                f"UPDATE {table} SET {column} = '{new}' WHERE {column} = '{old}'"
            )
    for old, new in pairs:
        op.execute(
            "UPDATE bedrock_agent_profile_prompts "
            f"SET profile_id = '{new}' WHERE profile_id = '{old}'"
        )


def upgrade() -> None:
    _rewrite(_RENAMES)


def downgrade() -> None:
    _rewrite([(new, old) for old, new in _RENAMES])
