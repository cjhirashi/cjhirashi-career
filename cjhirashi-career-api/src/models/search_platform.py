"""
SearchPlatform Model - Job search platforms (LinkedIn, GetOnBoard, etc.) where
a profile is maintained during the search. Vacancies sourced from a platform's
profile link back to it via Vacancy.search_platform_id.
Career domain (v2) - Operativa de Búsqueda.
"""
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.sql import func
from database import Base


from services.id_generator import register_id_listener


class SearchPlatform(Base):
    """A job-search platform/board and the profile maintained on it."""

    __tablename__ = "search_platforms"

    # --- Identificación (id prefijado + user_id para aislamiento) ---
    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # --- Campos de negocio ---
    name = Column(String(100), nullable=False)
    profile_url = Column(String(500), nullable=True)
    username = Column(String(255), nullable=True)
    # Cuenta de correo con la que está registrado este perfil (p.ej. gmail
    # personal vs. el de cjhirashi.com) - permite saber qué bandeja vigilar
    # por plataforma (Paulina depende de esto para dar seguimiento).
    account_email = Column(String(255), nullable=True)
    # FK a cv_versions: el CV que se subió al registrarse en esta plataforma
    # (muchas piden un CV al crear el perfil).
    cv_version_id = Column(
        String(20), ForeignKey("cv_versions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    profile_headline = Column(String(500), nullable=True)
    profile_notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=True)
    last_updated_at = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)

    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<SearchPlatform(id={self.id}, name='{self.name}')>"

register_id_listener(SearchPlatform, "spf")
