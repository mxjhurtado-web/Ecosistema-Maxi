"""
Conversation model - Core conversation entity.
"""
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database import Base


class ConversationStatus(str, enum.Enum):
    """Conversation status enumeration."""
    NEW = "new"
    TRIAGE = "triage"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    PENDING_CUSTOMER = "pending_customer"
    PENDING_AGENT = "pending_agent"
    CLOSED = "closed"


class ConversationPriority(str, enum.Enum):
    """Conversation priority enumeration."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Conversation(Base):
    """Conversation model."""
    
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    channel = Column(Enum("whatsapp", "chat_app", name="channel_enum"), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"), index=True)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    status = Column(Enum(ConversationStatus), nullable=False, default=ConversationStatus.NEW, index=True)
    priority = Column(Enum(ConversationPriority), default=ConversationPriority.NORMAL)
    
    # Timestamps
    first_message_at = Column(DateTime(timezone=True))
    first_response_at = Column(DateTime(timezone=True))
    assigned_at = Column(DateTime(timezone=True))
    closed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Close info
    closed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    close_reason = Column(String(100))
    
    # Metadata
    metadata = Column(JSONB, default={})
    
    # Relationships
    customer = relationship("Customer", back_populates="conversations")
    team = relationship("Team", back_populates="conversations")
    assigned_agent = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_conversations")
    closer = relationship("User", foreign_keys=[closed_by], back_populates="closed_conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    events = relationship("ConversationEvent", back_populates="conversation", cascade="all, delete-orphan")
    tags = relationship("ConversationTag", back_populates="conversation", cascade="all, delete-orphan")
    notes = relationship("ConversationNote", back_populates="conversation", cascade="all, delete-orphan")
    sla_violations = relationship("SLAViolation", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation {self.id} ({self.status})>"
