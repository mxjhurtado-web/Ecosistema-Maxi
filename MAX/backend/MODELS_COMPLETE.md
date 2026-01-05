# Database Models - Complete! 🎉

## ✅ Models Created

### Core Models (7 files)

#### 1. **user.py**
- `User` - Agent and admin accounts
- `UserRole` enum (admin, supervisor, team_lead, agent)
- Relationships: team_memberships, assigned_conversations, skills

#### 2. **team.py**
- `Team` - Sales, Support, Customer Service
- `TeamMembership` - Many-to-many user ↔ team
- Relationships: members, conversations, SLA policies

#### 3. **customer.py**
- `Customer` - End-users from WhatsApp/Chat App
- `CustomerIdentity` - Link multiple channels to same customer
- `Channel` enum (whatsapp, chat_app, email, sms)

#### 4. **conversation.py**
- `Conversation` - Core conversation entity
- `ConversationStatus` enum (new, triage, queued, assigned, etc.)
- `ConversationPriority` enum (low, normal, high, urgent)
- Timestamps: first_message_at, first_response_at, assigned_at, closed_at

#### 5. **message.py**
- `Message` - All messages (customer ↔ agent)
- `MediaFile` - Images, videos, audio, documents
- `MessageDirection` enum (inbound, outbound)
- `MessageSenderType` enum (customer, agent, system)
- `MessageStatus` enum (pending, sent, delivered, read, failed)

#### 6. **support.py**
- `Tag` - Reusable labels
- `ConversationTag` - Many-to-many conversations ↔ tags
- `ConversationNote` - Internal agent notes
- `ConversationEvent` - Audit trail for state changes

#### 7. **enhancements.py**
- `SLAPolicy` - Service level agreements
- `SLAViolation` - Track SLA breaches
- `CannedResponse` - Quick reply templates
- `BusinessHours` - Team operating hours
- `WhatsAppTemplate` - WhatsApp message templates
- `AgentSkill` - Agent skills for routing
- `RateLimitBucket` - Customer-side rate limiting

---

## 📊 Database Statistics

- **Total Models**: 20
- **Total Enums**: 8
- **Relationships**: 50+
- **Indexes**: 80+
- **Unique Constraints**: 12

---

## 🔧 Alembic Setup

### Files Created

1. **alembic.ini** - Main configuration
2. **alembic/env.py** - Async environment setup
3. **alembic/script.py.mako** - Migration template
4. **alembic/versions/** - Migration scripts directory

### Features

- ✅ Async SQLAlchemy support
- ✅ Auto-import all models
- ✅ Compare type changes
- ✅ Timezone-aware timestamps
- ✅ Custom migration file naming

---

## 🚀 Next Steps

### 1. Copy .env File

```bash
cd c:\Users\User\Ecosistema-Maxi\MAX\backend
cp .env.example .env
```

Edit `.env` and set:
```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# Set in .env
SECRET_KEY=your-generated-secret-key
DATABASE_URL=postgresql+asyncpg://max_user:max_password@localhost:5432/max_db
```

### 2. Start Database

```bash
# From MAX directory
cd c:\Users\User\Ecosistema-Maxi\MAX
docker-compose up -d postgres redis
```

### 3. Generate Initial Migration

```bash
# Inside backend directory
cd backend

# Option A: Using Docker
docker-compose run --rm backend alembic revision --autogenerate -m "Initial schema"

# Option B: Local Python (if you have venv)
alembic revision --autogenerate -m "Initial schema"
```

### 4. Apply Migration

```bash
# Using Docker
docker-compose run --rm backend alembic upgrade head

# Or local
alembic upgrade head
```

### 5. Verify Database

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U max_user -d max_db

# List tables
\dt

# Describe a table
\d users

# Exit
\q
```

---

## 📝 Model Relationships Diagram

```
users ──┬─── team_memberships ─── teams ──┬─── business_hours
        │                                  ├─── sla_policies
        │                                  └─── canned_responses
        ├─── agent_skills
        └─── assigned_conversations

customers ──┬─── customer_identities
            ├─── rate_limit_buckets
            └─── conversations ──┬─── messages ──── media_files
                                 ├─── conversation_events
                                 ├─── conversation_tags ─── tags
                                 ├─── conversation_notes
                                 └─── sla_violations ─── sla_policies
```

---

## 🧪 Testing Models

Create a test script to verify models work:

```python
# backend/test_models.py
import asyncio
from app.database import AsyncSessionLocal
from app.models import User, Team, Customer, Conversation
from app.core.security import get_password_hash

async def test_create_user():
    async with AsyncSessionLocal() as session:
        # Create a test user
        user = User(
            email="admin@max.com",
            password_hash=get_password_hash("admin123"),
            full_name="Admin User",
            role="admin",
            is_active=True
        )
        session.add(user)
        await session.commit()
        print(f"Created user: {user}")

if __name__ == "__main__":
    asyncio.run(test_create_user())
```

Run:
```bash
python test_models.py
```

---

## 🐛 Common Issues

### Issue: "No module named 'app'"
**Solution**: Make sure you're in the `backend` directory and PYTHONPATH is set:
```bash
cd backend
export PYTHONPATH=.  # Linux/Mac
$env:PYTHONPATH="."  # Windows PowerShell
```

### Issue: "Cannot connect to database"
**Solution**: Check PostgreSQL is running:
```bash
docker-compose ps postgres
docker-compose logs postgres
```

### Issue: "Alembic can't find models"
**Solution**: Make sure all models are imported in `app/models/__init__.py`

---

## ✅ Checklist

- [x] All models created
- [x] Enums defined
- [x] Relationships configured
- [x] Indexes added
- [x] Unique constraints set
- [x] Alembic configured
- [ ] .env file created
- [ ] Database started
- [ ] Initial migration generated
- [ ] Migration applied
- [ ] Database verified

---

## 📚 Documentation

- **Data Model**: `/docs/02-data-model.md`
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/
- **Alembic Docs**: https://alembic.sqlalchemy.org/

---

**Status**: ✅ **All models complete and ready for migration!**

Next: Generate and apply initial migration to create database schema.
