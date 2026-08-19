"""
LinkedInConnection Model - stores the OAuth access token issued after the
user authorizes the "Share on LinkedIn" self-serve product.

LinkedIn's self-serve OAuth app does not issue a refresh token (that
requires Marketing Developer Platform partner approval), so `access_token`
simply expires after `expires_at` and the user re-authorizes via the
Connect flow again - there is no silent renewal.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from database import Base


class LinkedInConnection(Base):
    """One active LinkedIn connection per user (singleton per user_id)."""

    __tablename__ = "linkedin_connections"
    __table_args__ = (UniqueConstraint("user_id"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    access_token = Column(String(2048), nullable=False)
    member_sub = Column(String(255), nullable=False)  # LinkedIn OIDC `sub` claim -> urn:li:person:{sub}
    member_name = Column(String(255), nullable=True)
    member_email = Column(String(255), nullable=True)
    profile_picture_url = Column(String(1024), nullable=True)

    expires_at = Column(DateTime(timezone=True), nullable=False)
    connected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<LinkedInConnection(user_id={self.user_id}, member_name='{self.member_name}')>"
