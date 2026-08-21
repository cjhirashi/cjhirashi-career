"""Consolidate CVVersion's 4 rigid text fields into one free-form Markdown `content` field

Carlos wants to restructure a CV version's body freely in Markdown instead
of being locked into 4 fixed slots (featured_achievement, executive_summary,
key_competencies, key_experience). Existing data isn't discarded: each row's
non-empty old fields are concatenated into Markdown sections and backfilled
into the new `content` column before the old columns are dropped.

Revision ID: ca159800797a
Revises:
Create Date: 2026-08-21

"""
import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "ca159800797a"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _build_content(featured_achievement, executive_summary, key_competencies, key_experience) -> Union[str, None]:
    """Markdown concatenation used for the one-time backfill - mirrors the
    format Carlos specified, skipping any section whose source field is
    NULL/empty. Returns None (-> NULL) if all 4 sources are empty."""
    sections: list[tuple[str, str]] = []

    if featured_achievement and featured_achievement.strip():
        sections.append(("Logro destacado", featured_achievement.strip()))

    if executive_summary and executive_summary.strip():
        sections.append(("Resumen ejecutivo", executive_summary.strip()))

    if key_competencies and key_competencies.strip():
        sections.append(("Competencias clave", key_competencies.strip()))

    if key_experience:  # NULL or [] both falsy - nothing worth keeping
        body = "```json\n" + json.dumps(key_experience, indent=2, ensure_ascii=False) + "\n```"
        sections.append(("Experiencia clave", body))

    if not sections:
        return None

    return "\n\n".join(f"## {header}\n\n{body}" for header, body in sections)


def upgrade() -> None:
    bind = op.get_bind()

    op.add_column("cv_versions", sa.Column("content", sa.Text(), nullable=True))

    rows = bind.execute(
        sa.text(
            "SELECT id, featured_achievement, executive_summary, key_competencies, key_experience "
            "FROM cv_versions"
        )
    ).fetchall()

    backfilled = 0
    for row in rows:
        content = _build_content(
            row.featured_achievement, row.executive_summary, row.key_competencies, row.key_experience
        )
        if content is not None:
            bind.execute(
                sa.text("UPDATE cv_versions SET content = :content WHERE id = :id"),
                {"content": content, "id": row.id},
            )
            backfilled += 1

    print(f"[ca159800797a] cv_versions: backfilled `content` for {backfilled}/{len(rows)} row(s)")

    op.drop_column("cv_versions", "featured_achievement")
    op.drop_column("cv_versions", "executive_summary")
    op.drop_column("cv_versions", "key_competencies")
    op.drop_column("cv_versions", "key_experience")


def downgrade() -> None:
    # Lossy on purpose: the 4 old fields were a rigid split of the same
    # information now free-form in `content`, and there's no reliable way to
    # un-concatenate Markdown back into them. Columns are restored empty.
    op.add_column("cv_versions", sa.Column("featured_achievement", sa.Text(), nullable=True))
    op.add_column("cv_versions", sa.Column("executive_summary", sa.Text(), nullable=True))
    op.add_column("cv_versions", sa.Column("key_competencies", sa.Text(), nullable=True))
    op.add_column(
        "cv_versions",
        sa.Column("key_experience", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.drop_column("cv_versions", "content")
