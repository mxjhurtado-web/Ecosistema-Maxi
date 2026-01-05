"""
Message model - All messages (customer ↔ agent).
"""
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Integer, Text, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database import Base


class MessageDirection(str, enum.Enum):
    """Message direction enumeration."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageSenderType(str, enum.Enum):
    """Message sender type enumeration."""
    CUSTOMER = "customer"
    AGENT = "agent"
    SYSTEM = "system"


class MessageStatus(str, enum.Enum):
    """Message status enumeration."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class Message(Base):
    """Message model."""
    
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    channel_message_id = Column(String(255), unique=True, index=True)  # External ID from WhatsApp/Chat App
    
    # Message info
    direction = Column(Enum(MessageDirection), nullable=False)
    sender_type = Column(Enum(MessageSenderType), nullable=False)
    sender_id = Column(UUID(as_uuid=True))  # user_id if agent, customer_id if customer
    
    # Content
    content_type = Column(String(50), nullable=False, default="text")
    content_text = Column(Text)
    content_media_url = Column(Text)
    content_metadata = Column(JSONB, default={})
    
    # Status
    status = Column(Enum(MessageStatus), default=MessageStatus.SENT, index=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    delivered_at = Column(DateTime(timezone=True))
    read_at = Column(DateTime(timezone=True))
    failed_reason = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Metadata
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    media_files = relationship("MediaFile", back_populates="message", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Message {self.id} ({self.direction})>"


class MediaFile(Base):
    """Media file storage for messages."""
    
    __tablename__ = "media_files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    channel_media_id = Column(String(255))  # WhatsApp media ID
    media_type = Column(Enum("image", "video", "audio", "document", name="media_type_enum"), nullable=False)
    mime_type = Column(String(100))
    file_size_bytes = Column(BigInteger)
    original_filename = Column(String(255))
    storage_url = Column(Text, nullable=False)  # S3/CloudFlare R2 URL
    storage_key = Column(String(500))  # S3 key for deletion
    thumbnail_url = Column(Text)
    expires_at = Column(DateTime(timezone=True), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    message = relationship("Message", back_populates="media_files")
    
    def __repr__(self):
        return f"<MediaFile {self.media_type} for message {self.message_id}>"
