"""
CoverLetterVersion Model - Versioned cover letters tailored to target roles/vacancies.
Career domain (v2) - Búsqueda.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from database import Base


class CoverLetterVersion(Base):
    """
    A cover letter version tailored to a target role and/or vacancy.

    NOTE: same `file_upload_id` discrepancy as `CVVersion` - see that model
    docstring.
    """

    __tablename__ = "cover_letter_versions"
    __table_args__ = (CheckConstraint("status IN ('draft', 'approved', 'final')"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    target_role_id = Column(Integer, ForeignKey("target_roles.id", ondelete="SET NULL"), nullable=True)
    target_vacancy_id = Column(Integer, ForeignKey("vacancies.id", ondelete="SET NULL"), nullable=True)

    title = Column(String(255), nullable=False)
    status = Column(String(30), default="draft", nullable=True, index=True)
    body_content = Column(Text, nullable=True)
    file_upload_id = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<CoverLetterVersion(id={self.id}, title='{self.title}')>"
