"""
TargetRole Model - Roles the user is targeting in their job search.
Career domain (v2) - Identity.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Date, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from database import Base


class TargetRole(Base):
    """A target role, with market validation data and priority."""

    __tablename__ = "target_roles"
    __table_args__ = (CheckConstraint("priority_order BETWEEN 1 AND 3"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    role_name = Column(String(255), nullable=False)
    priority_order = Column(Integer, nullable=True, index=True)
    salary_median = Column(Integer, nullable=True)
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    years_experience_required = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    market_active_vacancies = Column(Integer, nullable=True)
    market_validated_at = Column(Date, nullable=True)
    market_sources = Column(JSONB, nullable=True)
    current_accessibility = Column(String(100), nullable=True)
    key_requirements = Column(JSONB, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<TargetRole(id={self.id}, role_name='{self.role_name}')>"
