"""
WorkHistory Model - Past positions / employment history.
Career domain (v2) - Identity.
"""
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from database import Base


from services.id_generator import register_id_listener


class WorkHistory(Base):
    """A position held by the user at a company."""

    __tablename__ = "work_history"

    # --- Identificación (id prefijado + user_id para aislamiento) ---
    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # --- Campos de negocio ---
    company = Column(String(255), nullable=False)
    role_title = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=True, index=True)
    end_date = Column(Date, nullable=True)
    people_managed = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    narrative = Column(Text, nullable=True)
    achievements = Column(Text, nullable=True)
    key_metrics = Column(JSONB, nullable=True)
    learnings = Column(Text, nullable=True)
    contract_type = Column(String(50), nullable=True)
    industry_sector = Column(String(100), nullable=True)

    notes = Column(Text, nullable=True)


    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<WorkHistory(id={self.id}, company='{self.company}', role_title='{self.role_title}')>"

register_id_listener(WorkHistory, "wkh")
