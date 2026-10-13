"""
Vacancy Model - Job vacancies tracked during the search.
Career domain (v2) - Búsqueda.

NOTE: Replaces the legacy `models/vacancy.py` (deleted), whose columns did
not match the real `vacancies` table (it had already caused a table
collision; the table was dropped and recreated with this schema).
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Date, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from database import Base


from services.id_generator import register_id_listener
from services.vacancy_stage import DEFAULT_PROCESS_STAGE, PROCESS_STAGES


class Vacancy(Base):
    """A job vacancy found during the search, with fit scoring and evaluation."""

    __tablename__ = "vacancies"
    __table_args__ = (
        CheckConstraint("fit_percentage BETWEEN 0 AND 100"),
        CheckConstraint("evaluation IN ('apply', 'do_not_apply', 'pending_review')"),
        # Un solo canon: el catálogo vive en services.vacancy_stage (spec 007, RF-006).
        CheckConstraint(
            "process_stage IN (" + ", ".join(f"'{s}'" for s in PROCESS_STAGES) + ")",
            name="ck_vacancies_process_stage",
        ),
    )

    # --- Identificación (id prefijado + user_id para aislamiento) ---
    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # --- Campos de negocio ---
    order_number = Column(Integer, nullable=True)
    company = Column(String(255), nullable=False)
    # FK a target_companies (checklist Paulina #6): `company` sigue siendo
    # texto libre (vacantes de empresas fuera de la lista de target companies
    # también se registran), pero cuando sí corresponde a una target company
    # ya investigada, esto permite cruzar información de forma confiable.
    target_company_id = Column(
        String(20), ForeignKey("target_companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
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
    # --- Atributos nuevos (checklist Paulina #11) ---
    location = Column(String(255), nullable=True)
    work_modality = Column(String(100), nullable=True)
    seniority_level = Column(String(50), nullable=True)
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    required_skills = Column(JSONB, nullable=True)
    years_experience_required = Column(Integer, nullable=True)
    posted_date = Column(Date, nullable=True)
    # Etapa del proceso (spec 007). El estado (pending/in_process/closed) se calcula
    # a partir de ella y no se persiste.
    process_stage = Column(
        String(30),
        nullable=False,
        default=DEFAULT_PROCESS_STAGE,
        server_default=DEFAULT_PROCESS_STAGE,
        index=True,
    )
    process_stage_updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    priority = Column(String(10), nullable=True)
    contracting_model = Column(String(50), nullable=True)
    contact_id = Column(
        String(20), ForeignKey("networking_contacts.id", ondelete="SET NULL"), nullable=True
    )

    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Vacancy(id={self.id}, company='{self.company}', exact_role='{self.exact_role}')>"

register_id_listener(Vacancy, "vac")
