"""
User model - Agent and admin accounts.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration."""
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    TEAM_LEAD = "team_lead"
    AGENT = "agent"


class User(Base):
    """User model for agents and admins."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    keycloak_id = Column(String(255), unique=True, nullable=False, index=True)  # Keycloak user ID
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    team_memberships = relationship("TeamMembership", back_populates="user", cascade="all, delete-orphan")
    assigned_conversations = relationship("Conversation", foreign_keys="Conversation.assigned_to", back_populates="assigned_agent")
    closed_conversations = relationship("Conversation", foreign_keys="Conversation.closed_by", back_populates="closer")
    conversation_notes = relationship("ConversationNote", back_populates="author")
    agent_skills = relationship("AgentSkill", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
