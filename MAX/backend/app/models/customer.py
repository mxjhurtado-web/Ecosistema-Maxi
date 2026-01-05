"""
Customer model - End-users from WhatsApp or Chat App.
"""
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database import Base


class Channel(str, enum.Enum):
    """Communication channel enumeration."""
    WHATSAPP = "whatsapp"
    CHAT_APP = "chat_app"
    EMAIL = "email"
    SMS = "sms"


class Customer(Base):
    """Customer model for end-users."""
    
    __tablename__ = "customers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id = Column(String(255), unique=True, nullable=False, index=True)
    channel = Column(Enum(Channel), nullable=False, index=True)
    name = Column(String(255))
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    conversations = relationship("Conversation", back_populates="customer", cascade="all, delete-orphan")
    identities = relationship("CustomerIdentity", back_populates="customer", cascade="all, delete-orphan")
    rate_limit_buckets = relationship("RateLimitBucket", back_populates="customer", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Customer {self.external_id} ({self.channel})>"


class CustomerIdentity(Base):
    """Link multiple identities to same customer."""
    
    __tablename__ = "customer_identities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    channel = Column(Enum(Channel), nullable=False)
    external_id = Column(String(255), nullable=False)
    is_primary = Column(Boolean, default=False, index=True)
    verified_at = Column(DateTime(timezone=True))
    linked_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    customer = relationship("Customer", back_populates="identities")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('channel', 'external_id', name='uq_channel_external_id'),
    )
    
    def __repr__(self):
        return f"<CustomerIdentity {self.channel}:{self.external_id}>"
