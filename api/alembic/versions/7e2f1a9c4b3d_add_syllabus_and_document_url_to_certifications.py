"""Add syllabus (Markdown) and document_url to certifications

Carlos wants to attach a syllabus (temario, freeform Markdown) and a link
to the certificate document itself (PDF or image, hosted elsewhere - just
a URL, not a file upload) to each certification record.

Revision ID: 7e2f1a9c4b3d
Revises: ca159800797a
Create Date: 2026-08-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "7e2f1a9c4b3d"
down_revision: Union[str, None] = "ca159800797a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("certifications", sa.Column("syllabus", sa.Text(), nullable=True))
    op.add_column("certifications", sa.Column("document_url", sa.String(length=1000), nullable=True))


def downgrade() -> None:
    op.drop_column("certifications", "document_url")
    op.drop_column("certifications", "syllabus")
