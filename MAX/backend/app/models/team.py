"""
Team model - Sales, Support, Customer Service.
"""
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Team(Base):
    """Team model for organizing agents."""
    
    __tablename__ = "teams"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    team_memberships = relationship("TeamMembership", back_populates="team", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="team")
    tags = relationship("Tag", back_populates="team")
    sla_policies = relationship("SLAPolicy", back_populates="team", cascade="all, delete-orphan")
    business_hours = relationship("BusinessHours", back_populates="team", cascade="all, delete-orphan")
    canned_responses = relationship("CannedResponse", back_populates="team", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Team {self.name}>"


class TeamMembership(Base):
    """Many-to-many relationship between users and teams."""
    
    __tablename__ = "team_memberships"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    team_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Foreign keys
    from sqlalchemy import ForeignKey
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="team_memberships")
    team = relationship("Team", back_populates="team_memberships")
    
    # Unique constraint
    from sqlalchemy import UniqueConstraint
    __table_args__ = (
        UniqueConstraint('user_id', 'team_id', name='uq_user_team'),
    )
    
    def __repr__(self):
        return f"<TeamMembership user={self.user_id} team={self.team_id}>"
