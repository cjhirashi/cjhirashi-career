"""
BedrockConversation / BedrockConversationMessage — historial de chat en PostgreSQL.

Mismo `session_id` en cliente y servidor (UUID). Una fila por conversación;
los mensajes viven en bedrock_conversation_messages. Ver history_manager.py.
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

from services.id_generator import register_id_listener


class BedrockConversation(Base):
    __tablename__ = "bedrock_conversations"
    __table_args__ = (
        Index(
            "ix_bedrock_conversations_user_type_profile",
            "user_id",
            "session_type",
            "agent_profile_id",
        ),
    )

    # --- Identificación (id prefijado + user_id para aislamiento) ---
    id = Column(String(20), primary_key=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # --- Campos de negocio ---
    session_id = Column(String(100), nullable=False, unique=True, index=True)
    # contextual = sidebar derecha por sección; general = /agent/chat orquestador
    session_type = Column(String(20), nullable=False, default="contextual", index=True)
    # Especialista dueño de esta sesión (identity, search, orchestrator, …).
    # Cada agente tiene su propia lista; NULL = conversaciones previas al aislamiento.
    agent_profile_id = Column(String(50), nullable=True, index=True)
    title = Column(String(255), nullable=False, default="Nueva conversación")
    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True)

    messages = relationship(
        "BedrockConversationMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="BedrockConversationMessage.created_at"
    )

    def __repr__(self):
        return f"<BedrockConversation(id={self.id}, session_id='{self.session_id}')>"


class BedrockConversationMessage(Base):
    __tablename__ = "bedrock_conversation_messages"

    id = Column(String(20), primary_key=True)
    conversation_id = Column(String(20), ForeignKey("bedrock_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user" | "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    conversation = relationship("BedrockConversation", back_populates="messages")

    def __repr__(self):
        return f"<BedrockConversationMessage(id={self.id}, role='{self.role}')>"


register_id_listener(BedrockConversation, "bco")
register_id_listener(BedrockConversationMessage, "bcm")
