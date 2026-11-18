from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    title = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    messages = relationship(
        "Message", back_populates="conversation", order_by="Message.created_at"
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    is_sufficient = Column(Integer, nullable=True)  # 1=True, 0=False, NULL=N/A (user msgs)
    attempts = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    conversation = relationship("Conversation", back_populates="messages")
