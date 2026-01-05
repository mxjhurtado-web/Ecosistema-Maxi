"""
Enhancement models - SLA, Canned Responses, Business Hours, etc.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean, Time, Enum, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database import Base


# ===== SLA Models =====

class SLAPolicy(Base):
    """Service Level Agreement definitions."""
    
    __tablename__ = "sla_policies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    priority = Column(Enum("low", "normal", "high", "urgent", name="priority_enum"), nullable=False)
    frt_target_seconds = Column(Integer, nullable=False)
    resolution_target_seconds = Column(Integer, nullable=False)
    escalation_after_seconds = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    team = relationship("Team", back_populates="sla_policies")
    violations = relationship("SLAViolation", back_populates="sla_policy", cascade="all, delete-orphan")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('team_id', 'priority', name='uq_team_priority'),
    )
    
    def __repr__(self):
        return f"<SLAPolicy team={self.team_id} priority={self.priority}>"


class SLAViolation(Base):
    """Track SLA breaches."""
    
    __tablename__ = "sla_violations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sla_policy_id = Column(UUID(as_uuid=True), ForeignKey("sla_policies.id", ondelete="CASCADE"), nullable=False)
    violation_type = Column(Enum("frt", "resolution", name="violation_type_enum"), nullable=False)
    target_seconds = Column(Integer, nullable=False)
    actual_seconds = Column(Integer, nullable=False)
    escalated_to = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    escalated_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="sla_violations")
    sla_policy = relationship("SLAPolicy", back_populates="violations")
    
    def __repr__(self):
        return f"<SLAViolation {self.violation_type} for {self.conversation_id}>"


# ===== Canned Responses =====

class CannedResponse(Base):
    """Pre-defined quick replies for agents."""
    
    __tablename__ = "canned_responses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), index=True)
    shortcut = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    language = Column(String(10), default="es")
    category = Column(String(100), index=True)
    usage_count = Column(Integer, default=0)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    team = relationship("Team", back_populates="canned_responses")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('team_id', 'shortcut', name='uq_team_shortcut'),
    )
    
    def __repr__(self):
        return f"<CannedResponse {self.shortcut}>"


# ===== Business Hours =====

class BusinessHours(Base):
    """Team operating hours."""
    
    __tablename__ = "business_hours"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    open_time = Column(Time, nullable=False)
    close_time = Column(Time, nullable=False)
    timezone = Column(String(50), default="America/Mexico_City")
    is_active = Column(Boolean, default=True)
    
    # Relationships
    team = relationship("Team", back_populates="business_hours")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('team_id', 'day_of_week', name='uq_team_day'),
    )
    
    def __repr__(self):
        return f"<BusinessHours team={self.team_id} day={self.day_of_week}>"


# ===== WhatsApp Templates =====

class WhatsAppTemplate(Base):
    """WhatsApp message templates."""
    
    __tablename__ = "whatsapp_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    language = Column(String(10), nullable=False)
    category = Column(Enum("MARKETING", "UTILITY", "AUTHENTICATION", name="template_category_enum"), nullable=False)
    status = Column(Enum("PENDING", "APPROVED", "REJECTED", name="template_status_enum"), nullable=False, index=True)
    components = Column(JSONB, nullable=False)
    whatsapp_template_id = Column(String(255))
    rejection_reason = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('name', 'language', name='uq_name_language'),
    )
    
    def __repr__(self):
        return f"<WhatsAppTemplate {self.name} ({self.status})>"


# ===== Agent Skills =====

class AgentSkill(Base):
    """Agent skills for routing."""
    
    __tablename__ = "agent_skills"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_name = Column(String(100), nullable=False, index=True)
    proficiency_level = Column(Integer, nullable=False)  # 1-5
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="agent_skills")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('user_id', 'skill_name', name='uq_user_skill'),
    )
    
    def __repr__(self):
        return f"<AgentSkill {self.skill_name} level={self.proficiency_level}>"


# ===== Rate Limiting =====

class RateLimitBucket(Base):
    """Customer-side rate limiting."""
    
    __tablename__ = "rate_limit_buckets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    bucket_type = Column(Enum("message", "conversation", name="bucket_type_enum"), nullable=False)
    count = Column(Integer, default=0)
    window_start = Column(DateTime(timezone=True), nullable=False)
    window_end = Column(DateTime(timezone=True), nullable=False, index=True)
    is_blocked = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    customer = relationship("Customer", back_populates="rate_limit_buckets")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('customer_id', 'bucket_type', 'window_start', name='uq_customer_bucket_window'),
    )
    
    def __repr__(self):
        return f"<RateLimitBucket {self.bucket_type} count={self.count}>"
