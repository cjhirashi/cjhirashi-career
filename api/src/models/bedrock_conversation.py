"""
BedrockConversation / BedrockConversationMessage - server-side conversation
history for Agent Bedrock, so it's the same from any device Carlos logs in
from (the harness's own session memory is not something we can list/browse
by title, and the earlier client-only localStorage version didn't survive
switching devices).

`session_id` is the same id already used for `invoke_harness`'s
`runtimeSessionId` (see bedrock_service.chat_stream) - one row per
conversation, keyed by the id the harness itself uses, not a separate one.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class BedrockConversation(Base):
    __tablename__ = "bedrock_conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(100), nullable=False, unique=True, index=True)
    title = Column(String(255), nullable=False, default="Nueva conversación")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True)

    messages = relationship(
        "BedrockConversationMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="BedrockConversationMessage.created_at"
    )

    def __repr__(self):
        return f"<BedrockConversation(id={self.id}, session_id='{self.session_id}')>"


class BedrockConversationMessage(Base):
    __tablename__ = "bedrock_conversation_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("bedrock_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user" | "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    conversation = relationship("BedrockConversation", back_populates="messages")

    def __repr__(self):
        return f"<BedrockConversationMessage(id={self.id}, role='{self.role}')>"
