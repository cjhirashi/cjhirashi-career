"""
Certification Model - Professional certifications.
Career domain (v2) - Identity.
"""
from sqlalchemy import CheckConstraint, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


from services.id_generator import register_id_listener


class Certification(Base):
    """Certification earned by the user, optionally linked to a competency."""

    __tablename__ = "certifications"
    __table_args__ = (CheckConstraint("status IN ('pending', 'in_progress', 'completed')"),)

    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    institution = Column(String(255), nullable=True)
    year = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    syllabus = Column(Text, nullable=True)
    document_url = Column(String(1000), nullable=True)
    status = Column(String(30), default="pending", nullable=True, index=True)
    related_competency_id = Column(String(20), ForeignKey("competencies.id", ondelete="SET NULL"), nullable=True)

    notes = Column(Text, nullable=True)


    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Certification(id={self.id}, name='{self.name}')>"

register_id_listener(Certification, "crt")
