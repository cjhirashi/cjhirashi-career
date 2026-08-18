"""
TargetCompany Model - Companies targeted in the job search, tiered by priority.
Career domain (v2) - Búsqueda.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


class TargetCompany(Base):
    """A company the user is targeting, with fit and networking context."""

    __tablename__ = "target_companies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    company_name = Column(String(255), nullable=False)
    tier = Column(Integer, nullable=True, index=True)
    best_fit_role_id = Column(Integer, ForeignKey("target_roles.id", ondelete="SET NULL"), nullable=True)
    company_size = Column(String(50), nullable=True)
    salary_estimate = Column(String(100), nullable=True)
    work_modality = Column(String(100), nullable=True)
    target_market = Column(String(100), nullable=True)
    weak_tie_contact_id = Column(Integer, ForeignKey("networking_contacts.id", ondelete="SET NULL"), nullable=True)
    priority = Column(String(10), nullable=True)
    status = Column(String(30), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<TargetCompany(id={self.id}, company_name='{self.company_name}')>"
