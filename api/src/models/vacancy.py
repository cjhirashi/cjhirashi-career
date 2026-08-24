"""
Vacancy Model - Job vacancies tracked during the search.
Career domain (v2) - Búsqueda.

NOTE: Replaces the legacy `models/vacancy.py` (deleted), whose columns did
not match the real `vacancies` table (it had already caused a table
collision; the table was dropped and recreated with this schema).
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Date, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from database import Base


from services.id_generator import register_id_listener


class Vacancy(Base):
    """A job vacancy found during the search, with fit scoring and evaluation."""

    __tablename__ = "vacancies"
    __table_args__ = (
        CheckConstraint("fit_percentage BETWEEN 0 AND 100"),
        CheckConstraint("evaluation IN ('apply', 'do_not_apply', 'pending_review')"),
    )

    # --- Identificación (id prefijado + user_id para aislamiento) ---
    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # --- Campos de negocio ---
    order_number = Column(Integer, nullable=True)
    company = Column(String(255), nullable=False)
    exact_role = Column(String(255), nullable=False)
    vacancy_url = Column(String(500), unique=True, nullable=True)
    source = Column(String(50), nullable=True)
    found_date = Column(Date, nullable=True)
    fit_percentage = Column(Integer, nullable=True, index=True)
    track_category = Column(String(50), nullable=True)
    recommended_cv_version = Column(String(100), nullable=True)
    analysis_notes = Column(Text, nullable=True)
    evaluation = Column(String(30), default="pending_review", nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=True)

    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Vacancy(id={self.id}, company='{self.company}', exact_role='{self.exact_role}')>"

register_id_listener(Vacancy, "vac")
