"""
CVVersion Model - Versioned CVs tailored to target roles/vacancies.
Career domain (v2) - Búsqueda.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint, JSON
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import func
from database import Base



from services.id_generator import register_id_listener


class CVVersion(Base):
    """
    A CV version tailored to a target role.

    NOTE: `file_upload_id` has a real DB foreign key to the legacy singular
    `file_upload` table (from init.sql), not to the `file_uploads` table
    used by the active `FileUpload` model. This is a known discrepancy in
    the base schema (see project report) - not modeled as a SQLAlchemy
    ForeignKey here to avoid coupling to the wrong table.
    """

    __tablename__ = "cv_versions"
    __table_args__ = (CheckConstraint("status IN ('draft', 'approved', 'final')"),)

    # --- Identificación (id prefijado + user_id para aislamiento) ---
    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # --- Campos de negocio ---
    target_role_id = Column(String(20), ForeignKey("target_roles.id", ondelete="SET NULL"), nullable=True)

    title = Column(String(255), nullable=False)
    length_pages = Column(Integer, nullable=True)
    status = Column(String(30), default="draft", nullable=True, index=True)
    # Free-form Markdown - replaces the old executive_summary/key_competencies/
    # key_experience/featured_achievement fields (2026-08-21 migration) so the
    # content can be restructured freely instead of fitting 4 rigid slots.
    content = Column(Text, nullable=True)
    target_vacancy_ids = Column(
        JSON().with_variant(postgresql.JSONB, "postgresql"), nullable=True)
    file_upload_id = Column(String(20), nullable=True)

    notes = Column(Text, nullable=True)


    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<CVVersion(id={self.id}, title='{self.title}')>"

register_id_listener(CVVersion, "cvv")
