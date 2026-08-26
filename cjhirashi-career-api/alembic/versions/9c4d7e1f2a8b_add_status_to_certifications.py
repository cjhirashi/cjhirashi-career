"""Add status to certifications

Carlos wants to track a certification's progress: pending (not started),
in_progress, or completed. Defaults existing rows to 'completed' - a
certification record only existed in the first place because it was
already earned, so treating pre-existing rows as anything else would
misrepresent them.

Revision ID: 9c4d7e1f2a8b
Revises: 7e2f1a9c4b3d
Create Date: 2026-08-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "9c4d7e1f2a8b"
down_revision: Union[str, None] = "7e2f1a9c4b3d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("certifications", sa.Column("status", sa.String(length=30), nullable=True))
    op.execute("UPDATE certifications SET status = 'completed'")
    op.create_check_constraint(
        "certifications_status_check",
        "certifications",
        "status IN ('pending', 'in_progress', 'completed')",
    )
    op.create_index(op.f("ix_certifications_status"), "certifications", ["status"])


def downgrade() -> None:
    op.drop_index(op.f("ix_certifications_status"), table_name="certifications")
    op.drop_constraint("certifications_status_check", "certifications", type_="check")
    op.drop_column("certifications", "status")
