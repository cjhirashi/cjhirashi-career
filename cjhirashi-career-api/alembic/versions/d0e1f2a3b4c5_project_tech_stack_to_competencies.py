"""Replace projects.tech_stack (free text) with projects.competency_ids (FK list).

`tech_stack` was a "one item per line" Markdown list, same convention as
`tags`/`approach_steps`. Carlos wants the admin's "Stack tecnológico" field
to reference real `competencies` rows instead - existing lines are migrated
into `competencies` (find-or-create by case-insensitive name, per user,
`type='technical'`) and `projects.competency_ids` (JSONB, same pattern as
`achievements.demonstrated_competency_ids`) collects the resulting ids.

Destructive: `tech_stack`'s original free text is not preserved anywhere
after this migration - `downgrade()` recreates an empty column, it does not
reconstruct the original lines.

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-08-27
"""
import re
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "d0e1f2a3b4c5"
down_revision: Union[str, tuple, None] = "c9d0e1f2a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _parse_lines(text):
    if not text:
        return []
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        line = re.sub(r"^[-*]\s+", "", line)
        if line:
            lines.append(line)
    return lines


def upgrade() -> None:
    bind = op.get_bind()
    columns = {c["name"] for c in sa.inspect(bind).get_columns("projects")}

    if "competency_ids" not in columns:
        op.add_column("projects", sa.Column("competency_ids", JSONB(), nullable=True))

    if "tech_stack" in columns:
        rows = bind.execute(
            sa.text("SELECT id, user_id, tech_stack FROM projects WHERE tech_stack IS NOT NULL")
        ).fetchall()

        for project_id, user_id, tech_stack in rows:
            names = _parse_lines(tech_stack)
            if not names:
                continue

            existing = bind.execute(
                sa.text("SELECT id, name FROM competencies WHERE user_id = :user_id"),
                {"user_id": user_id},
            ).fetchall()
            by_name = {name.lower(): comp_id for comp_id, name in existing}

            resolved_ids = []
            seen = set()
            for name in names:
                comp_id = by_name.get(name.lower())
                if comp_id is None:
                    next_id = bind.execute(sa.text("SELECT nextval('cmp_id_seq')")).scalar()
                    comp_id = f"cmp-{next_id}"
                    bind.execute(
                        sa.text(
                            "INSERT INTO competencies (id, user_id, name, type, created_at, updated_at) "
                            "VALUES (:id, :user_id, :name, 'technical', now(), now())"
                        ),
                        {"id": comp_id, "user_id": user_id, "name": name},
                    )
                    by_name[name.lower()] = comp_id
                if comp_id not in seen:
                    seen.add(comp_id)
                    resolved_ids.append(comp_id)

            bind.execute(
                sa.text("UPDATE projects SET competency_ids = :ids WHERE id = :id").bindparams(
                    sa.bindparam("ids", type_=JSONB())
                ),
                {"ids": resolved_ids, "id": project_id},
            )

        op.drop_column("projects", "tech_stack")


def downgrade() -> None:
    columns = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("projects")}
    if "tech_stack" not in columns:
        op.add_column("projects", sa.Column("tech_stack", sa.Text(), nullable=True))
    if "competency_ids" in columns:
        op.drop_column("projects", "competency_ids")
