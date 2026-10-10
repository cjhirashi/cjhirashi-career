"""
TargetCompany Model - Companies targeted in the job search, tiered by priority.
Career domain (v2) - Búsqueda.
"""
from sqlalchemy import Column, Date, Float, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from database import Base


from services.id_generator import register_id_listener


class TargetCompany(Base):
    """A company the user is targeting, with fit and networking context."""

    __tablename__ = "target_companies"

    # --- Identificación (id prefijado + user_id para aislamiento) ---
    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # --- Campos de negocio ---
    company_name = Column(String(255), nullable=False)
    tier = Column(Integer, nullable=True, index=True)
    best_fit_role_id = Column(String(20), ForeignKey("target_roles.id", ondelete="SET NULL"), nullable=True)
    company_size = Column(String(50), nullable=True)
    salary_estimate = Column(String(100), nullable=True)
    work_modality = Column(String(100), nullable=True)
    target_market = Column(String(100), nullable=True)
    weak_tie_contact_id = Column(String(20), ForeignKey("networking_contacts.id", ondelete="SET NULL"), nullable=True)
    priority = Column(String(10), nullable=True)
    status = Column(String(30), nullable=True)
    notes = Column(Text, nullable=True)
    career_board_provider = Column(String(30), nullable=True)
    career_board_token = Column(String(100), nullable=True)
    # --- Atributos nuevos (checklist Paulina #10) ---
    industry_sector = Column(String(100), nullable=True)
    company_culture = Column(Text, nullable=True)
    # Alimenta el factor "Prestige/Brand" de fit_scoring_factors, que hoy no
    # tiene de dónde tomar el dato.
    funding_stage = Column(String(50), nullable=True)
    # Alimenta el factor "Technology Stack" de fit_scoring_factors.
    tech_stack = Column(JSONB, nullable=True)
    company_website = Column(String(500), nullable=True)
    linkedin_company_url = Column(String(500), nullable=True)
    hiring_velocity = Column(String(30), nullable=True)
    # Para saber qué registro está desactualizado.
    last_researched_at = Column(Date, nullable=True)
    # Rating externo (Glassdoor o similar), si está disponible.
    review_score = Column(Float, nullable=True)

    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<TargetCompany(id={self.id}, company_name='{self.company_name}')>"

register_id_listener(TargetCompany, "tco")
