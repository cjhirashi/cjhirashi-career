"""
Identity Model - Career identity and personal branding.
Stores IKIGAI, diferenciadores, narrativa, propuesta de valor.
"""
from sqlalchemy import Column, Integer, ForeignKey, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class Identity(Base):
    """
    Professional identity profile.

    Stores:
    - IKIGAI (passion, mission, vocation, profession)
    - Diferenciadores (unique strengths)
    - Narrativa profesional (professional story)
    - Propuesta de valor (value proposition)
    """

    __tablename__ = "identities"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Key
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # IKIGAI Components
    passion = Column(Text, nullable=True, help_text="What you love doing (passion)")
    mission = Column(Text, nullable=True, help_text="What you believe in (mission)")
    vocation = Column(Text, nullable=True, help_text="What you're good at (vocation)")
    profession = Column(Text, nullable=True, help_text="What the world needs (profession)")

    # Diferenciadores (Key Strengths)
    key_strengths = Column(Text, nullable=True, help_text="Top 3-5 unique strengths")
    unique_value_prop = Column(Text, nullable=True, help_text="What makes you different")

    # Professional Narrative
    professional_narrative = Column(Text, nullable=True, help_text="Your professional story in 3-4 sentences")
    career_objective = Column(Text, nullable=True, help_text="Long-term career goal")

    # Value Proposition
    value_proposition = Column(Text, nullable=True, help_text="Concise value statement for employers")
    elevator_pitch = Column(String(500), nullable=True, help_text="30-second pitch")

    # Extended Profile
    bio = Column(Text, nullable=True, help_text="Extended professional bio")
    about_me = Column(Text, nullable=True, help_text="About me section")

    # SEO & Branding
    keywords = Column(String(500), nullable=True, help_text="Comma-separated professional keywords")
    tagline = Column(String(255), nullable=True, help_text="Professional tagline")

    # Metadata
    extra_metadata = Column(JSON, nullable=True, help_text="Additional identity metadata")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="identity")

    def __repr__(self):
        return f"<Identity(id={self.id}, user_id={self.user_id})>"
