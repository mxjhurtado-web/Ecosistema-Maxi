"""
Supporting models for conversations - Tags, Notes, Events.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Tag(Base):
    """Reusable labels for conversations."""
    
    __tablename__ = "tags"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    color = Column(String(7), default="#3B82F6")
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), index=True)  # null = global
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    team = relationship("Team", back_populates="tags")
    conversation_tags = relationship("ConversationTag", back_populates="tag", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tag {self.name}>"


class ConversationTag(Base):
    """Many-to-many: conversations ↔ tags."""
    
    __tablename__ = "conversation_tags"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    tag_id = Column(UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), nullable=False, index=True)
    added_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="tags")
    tag = relationship("Tag", back_populates="conversation_tags")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('conversation_id', 'tag_id', name='uq_conversation_tag'),
    )
    
    def __repr__(self):
        return f"<ConversationTag conv={self.conversation_id} tag={self.tag_id}>"


class ConversationNote(Base):
    """Internal agent notes."""
    
    __tablename__ = "conversation_notes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    content = Column(Text, nullable=False)
    is_pinned = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="notes")
    author = relationship("User", back_populates="conversation_notes")
    
    def __repr__(self):
        return f"<ConversationNote for {self.conversation_id}>"


class ConversationEvent(Base):
    """Audit trail for state changes."""
    
    __tablename__ = "conversation_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    actor_type = Column(String(20))  # user, system, ai
    actor_id = Column(UUID(as_uuid=True), index=True)  # user_id or null for system
    old_value = Column(JSONB)
    new_value = Column(JSONB)
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="events")
    
    def __repr__(self):
        return f"<ConversationEvent {self.event_type} for {self.conversation_id}>"
