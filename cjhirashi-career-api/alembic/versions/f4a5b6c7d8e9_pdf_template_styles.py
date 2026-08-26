"""PDF template styles table + style_id FK on templates.

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
Create Date: 2026-08-24
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f4a5b6c7d8e9"
down_revision: Union[str, None] = "e3f4a5b6c7d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SEQUENCE IF NOT EXISTS pds_id_seq START 1")

    op.create_table(
        "pdf_template_styles",
        sa.Column("id", sa.String(length=20), nullable=False),
        sa.Column("user_id", sa.String(length=20), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("css_content", sa.Text(), nullable=False),
        sa.Column("style_guide", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pdf_template_styles_user_id", "pdf_template_styles", ["user_id"])
    op.create_index("ix_pdf_template_styles_slug", "pdf_template_styles", ["slug"])
    op.create_index("ix_pdf_template_styles_is_active", "pdf_template_styles", ["is_active"])

    op.add_column("pdf_output_templates", sa.Column("style_id", sa.String(length=20), nullable=True))
    op.add_column("pdf_output_templates", sa.Column("variables", sa.Text(), nullable=True))
    op.create_foreign_key(
        "fk_pdf_output_templates_style_id",
        "pdf_output_templates",
        "pdf_template_styles",
        ["style_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_pdf_output_templates_style_id", "pdf_output_templates", ["style_id"])

    # Migrate inline css_content into reusable style rows (one per template that had CSS).
    op.execute(
        """
        INSERT INTO pdf_template_styles (id, user_id, slug, title, description, css_content, style_guide, is_active)
        SELECT
            'pds-' || nextval('pds_id_seq'),
            t.user_id,
            t.slug || '-style',
            t.title || ' (estilo)',
            'Migrado automáticamente desde plantilla ' || t.slug,
            t.css_content,
            NULL,
            TRUE
        FROM pdf_output_templates t
        WHERE t.css_content IS NOT NULL AND btrim(t.css_content) <> ''
        """
    )

    op.execute(
        """
        UPDATE pdf_output_templates t
        SET style_id = s.id
        FROM pdf_template_styles s
        WHERE s.slug = t.slug || '-style'
          AND s.user_id = t.user_id
          AND t.css_content IS NOT NULL
          AND btrim(t.css_content) <> ''
        """
    )

    op.drop_column("pdf_output_templates", "css_content")


def downgrade() -> None:
    op.add_column("pdf_output_templates", sa.Column("css_content", sa.Text(), nullable=True))

    op.execute(
        """
        UPDATE pdf_output_templates t
        SET css_content = s.css_content
        FROM pdf_template_styles s
        WHERE t.style_id = s.id
        """
    )

    op.drop_constraint("fk_pdf_output_templates_style_id", "pdf_output_templates", type_="foreignkey")
    op.drop_index("ix_pdf_output_templates_style_id", table_name="pdf_output_templates")
    op.drop_column("pdf_output_templates", "variables")
    op.drop_column("pdf_output_templates", "style_id")

    op.drop_index("ix_pdf_template_styles_is_active", table_name="pdf_template_styles")
    op.drop_index("ix_pdf_template_styles_slug", table_name="pdf_template_styles")
    op.drop_index("ix_pdf_template_styles_user_id", table_name="pdf_template_styles")
    op.drop_table("pdf_template_styles")
    op.execute("DROP SEQUENCE IF EXISTS pds_id_seq")
