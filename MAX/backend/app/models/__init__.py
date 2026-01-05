"""
Models package - Import all models here for Alembic.
"""
from app.database import Base

# Import all models
from app.models.user import User, UserRole
from app.models.team import Team, TeamMembership
from app.models.customer import Customer, CustomerIdentity, Channel
from app.models.conversation import Conversation, ConversationStatus, ConversationPriority
from app.models.message import Message, MediaFile, MessageDirection, MessageSenderType, MessageStatus
from app.models.support import Tag, ConversationTag, ConversationNote, ConversationEvent
from app.models.enhancements import (
    SLAPolicy,
    SLAViolation,
    CannedResponse,
    BusinessHours,
    WhatsAppTemplate,
    AgentSkill,
    RateLimitBucket
)

# Export all models
__all__ = [
    "Base",
    "User",
    "UserRole",
    "Team",
    "TeamMembership",
    "Customer",
    "CustomerIdentity",
    "Channel",
    "Conversation",
    "ConversationStatus",
    "ConversationPriority",
    "Message",
    "MediaFile",
    "MessageDirection",
    "MessageSenderType",
    "MessageStatus",
    "Tag",
    "ConversationTag",
    "ConversationNote",
    "ConversationEvent",
    "SLAPolicy",
    "SLAViolation",
    "CannedResponse",
    "BusinessHours",
    "WhatsAppTemplate",
    "AgentSkill",
    "RateLimitBucket",
]
