"""
Application Model - Job applications submitted for a vacancy.
Career domain (v2) - Búsqueda.
"""
from sqlalchemy import Column, Integer, Text, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from database import Base


from services.id_generator import register_id_listener


class Application(Base):
    """A concrete application submitted for a vacancy."""

    __tablename__ = "applications"
    __table_args__ = (
        CheckConstraint(
            "current_status IN ('applied', 'in_process', 'offer', 'rejected', 'archived')"
        ),
        CheckConstraint(
            "final_result IN ('offer_accepted', 'offer_rejected', 'rejected', 'negotiating')"
        ),
    )

    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    vacancy_id = Column(String(20), ForeignKey("vacancies.id", ondelete="CASCADE"), nullable=False, index=True)
    cv_version_id = Column(String(20), ForeignKey("cv_versions.id", ondelete="SET NULL"), nullable=True)
    cover_letter_version_id = Column(String(20), ForeignKey("cover_letter_versions.id", ondelete="SET NULL"), nullable=True
    )
    recruiter_contact_id = Column(String(20), ForeignKey("networking_contacts.id", ondelete="SET NULL"), nullable=True
    )

    applied_at = Column(DateTime(timezone=True), nullable=True)
    current_status = Column(String(30), default="applied", nullable=True, index=True)
    final_result = Column(String(30), nullable=True)

    notes = Column(Text, nullable=True)


    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Application(id={self.id}, vacancy_id={self.vacancy_id}, status='{self.current_status}')>"

register_id_listener(Application, "apl")
