"""Add projects.slug, backfilled from title (portfolio links use it instead of id).

Revision ID: ca4ad88923c6
Revises: 1275560f7481
"""
import re
import unicodedata
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "ca4ad88923c6"
down_revision: Union[str, None] = "1275560f7481"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "projects"


def _slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns(_TABLE)}
    if "slug" not in columns:
        op.add_column(_TABLE, sa.Column("slug", sa.String(length=255), nullable=True))

    projects_table = sa.table("projects", sa.column("id", sa.String), sa.column("title", sa.String), sa.column("slug", sa.String))
    rows = bind.execute(sa.select(projects_table.c.id, projects_table.c.title).order_by(projects_table.c.id)).fetchall()

    used_slugs: set[str] = set()
    for project_id, title in rows:
        base = _slugify(title) or project_id
        slug = base
        suffix = 2
        while slug in used_slugs:
            slug = f"{base}-{suffix}"
            suffix += 1
        used_slugs.add(slug)
        bind.execute(projects_table.update().where(projects_table.c.id == project_id).values(slug=slug))


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns(_TABLE)}
    if "slug" in columns:
        op.drop_column(_TABLE, "slug")
