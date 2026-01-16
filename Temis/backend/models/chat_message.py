#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Chat Message model for TEMIS
Stores daily log chat conversations
"""

from sqlalchemy import Column, String, Text, DateTime, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from backend.database import Base


class ChatMessage(Base):
    """Chat message model for daily log conversations"""
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    message_date = Column(Date, nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    attachments = Column(JSON)  # List of attachment file paths/URLs
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project")
    user = relationship("User")

    def __repr__(self):
        return f"<ChatMessage {self.role}: {self.content[:50]}...>"
