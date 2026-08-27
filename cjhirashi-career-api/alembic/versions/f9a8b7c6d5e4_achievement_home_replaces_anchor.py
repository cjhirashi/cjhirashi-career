"""Replace projects.is_anchor with achievements.home.

The Home page's flagship block used to render the single `is_anchor`
project as a full case-study. Carlos wants that block to show a
highlighted achievement (`logro`) instead - `achievements.home` marks the
one achievement featured there, same "only one at a time, first match
wins if more are flagged" convention `is_anchor` used.

Indexes in this DB are hand-named `idx_<table>_<column>` (not SQLAlchemy's
`ix_` autogeneration convention), and `projects.is_anchor` was never
actually given one despite the model's `index=True` - so both index
operations here go through the inspector instead of assuming a name.

Revision ID: f9a8b7c6d5e4
Revises: d0e1f2a3b4c5
Create Date: 2026-08-27
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f9a8b7c6d5e4"
down_revision: Union[str, tuple, None] = "d0e1f2a3b4c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

HOME_INDEX = "idx_achievements_home"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    achievement_columns = {c["name"] for c in inspector.get_columns("achievements")}
    if "home" not in achievement_columns:
        op.add_column("achievements", sa.Column("home", sa.Boolean(), nullable=True, server_default=sa.false()))
        op.create_index(HOME_INDEX, "achievements", ["home"])

    project_columns = {c["name"] for c in inspector.get_columns("projects")}
    if "is_anchor" in project_columns:
        for index in inspector.get_indexes("projects"):
            if index["column_names"] == ["is_anchor"]:
                op.drop_index(index["name"], table_name="projects")
        op.drop_column("projects", "is_anchor")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    project_columns = {c["name"] for c in inspector.get_columns("projects")}
    if "is_anchor" not in project_columns:
        op.add_column("projects", sa.Column("is_anchor", sa.Boolean(), nullable=True, server_default=sa.false()))

    achievement_columns = {c["name"] for c in inspector.get_columns("achievements")}
    if "home" in achievement_columns:
        for index in inspector.get_indexes("achievements"):
            if index["column_names"] == ["home"]:
                op.drop_index(index["name"], table_name="achievements")
        op.drop_column("achievements", "home")
