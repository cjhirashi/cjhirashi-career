"""Singleton biographical card for the career manager.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-25
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    op.execute("CREATE SEQUENCE IF NOT EXISTS psp_id_seq START 1")

    if "personal_profile" not in inspector.get_table_names():
        op.create_table(
            "personal_profile",
            sa.Column("id", sa.String(length=20), nullable=False),
            sa.Column("user_id", sa.String(length=20), nullable=False),
            sa.Column("full_name", sa.String(length=255), nullable=False),
            sa.Column("preferred_name", sa.String(length=255), nullable=True),
            sa.Column("date_of_birth", sa.Date(), nullable=True),
            sa.Column("nationality", sa.String(length=100), nullable=True),
            sa.Column("city", sa.String(length=255), nullable=True),
            sa.Column("country", sa.String(length=100), nullable=True),
            sa.Column("phone", sa.String(length=40), nullable=True),
            sa.Column("email", sa.String(length=255), nullable=True),
            sa.Column("languages", sa.Text(), nullable=True),
            sa.Column("work_authorization", sa.Text(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id"),
        )
        op.create_index("ix_personal_profile_id", "personal_profile", ["id"])
        op.create_index("ix_personal_profile_user_id", "personal_profile", ["user_id"])

    # One row per existing user, prefilled with the account name/email/country
    # so the career manager has a reference card immediately. Date of birth
    # and the rest stay empty for Carlos to complete.
    op.execute(
        """
        INSERT INTO personal_profile (
            id, user_id, full_name, email, country, notes, created_at, updated_at
        )
        SELECT
            'psp-' || nextval('psp_id_seq'),
            u.id,
            COALESCE(NULLIF(btrim(u.full_name), ''), u.username),
            u.email,
            u.country,
            'Ficha de referencia del gestor de carrera. Completar fecha de nacimiento, ubicación, idiomas y autorización de trabajo.',
            NOW(),
            NOW()
        FROM users u
        WHERE NOT EXISTS (
            SELECT 1 FROM personal_profile p WHERE p.user_id = u.id
        )
        """
    )


def downgrade() -> None:
    op.drop_index("ix_personal_profile_user_id", table_name="personal_profile")
    op.drop_index("ix_personal_profile_id", table_name="personal_profile")
    op.drop_table("personal_profile")
    op.execute("DROP SEQUENCE IF EXISTS psp_id_seq")
