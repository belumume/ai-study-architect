"""
Chat Message model for persistent chat history
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, DateTime, ForeignKey, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class ChatMessage(Base):
    """Chat message model for persistent storage"""

    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_id = Column(String(255), nullable=False, index=True)

    # Message content
    role = Column(String(50), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)

    # Optional metadata
    metadata = Column(JSON, nullable=True)  # Store any additional metadata

    # Content references (if message was about specific content)
    content_ids = Column(JSON, nullable=True)  # List of content IDs referenced

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="chat_messages")

    def __repr__(self) -> str:
        return f"<ChatMessage {self.role} from session {self.session_id[:8]}...>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "role": self.role,
            "content": self.content,
            "timestamp": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.metadata,
            "content_ids": self.content_ids
        }
