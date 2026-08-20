"""
OperationalMethodology Model - protocols/frameworks that document HOW to work
across the career-domain tables and how they relate to each other (e.g. "a
change in Identity propagates to Competencies, Evidence, ..."). Content lives
in Markdown, authored the same convention as every other long-text field in
this app - see `content`. Not exposed on the public portal, admin-only.
Career domain (v2) - Soporte operativo.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


class OperationalMethodology(Base):
    __tablename__ = "operational_methodologies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    # e.g. "Investigación Operativa" / "Metodología Operativa de la Bóveda" -
    # free text rather than an enum, new top-level groupings will show up.
    section = Column(String(150), nullable=True, index=True)
    subsection = Column(String(150), nullable=True)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<OperationalMethodology(id={self.id}, title='{self.title}')>"
