"""
NetworkingActivity Model - Recurring networking activities (give/share/talk framework).
Career domain (v2) - Búsqueda.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from database import Base


from services.id_generator import register_id_listener


class NetworkingActivity(Base):
    """A recurring networking activity classified in the 70/20/10 framework."""

    __tablename__ = "networking_activities"
    __table_args__ = (
        CheckConstraint(
            "category IN ('give_value_70', 'share_learning_20', 'talk_about_you_10')"
        ),
    )

    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    category = Column(String(30), nullable=True, index=True)
    activity_type = Column(String(255), nullable=False)
    concrete_action = Column(Text, nullable=True)
    example = Column(Text, nullable=True)
    frequency_description = Column(String(100), nullable=True)
    times_completed = Column(Integer, default=0, nullable=True)
    is_active = Column(Boolean, default=True, nullable=True)

    notes = Column(Text, nullable=True)


    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<NetworkingActivity(id={self.id}, activity_type='{self.activity_type}')>"

register_id_listener(NetworkingActivity, "nwa")
