# MAX Backend

Backend API for MAX omnichannel inbox platform.

## Tech Stack

- **Python 3.11+**
- **FastAPI** - Modern web framework
- **SQLAlchemy** - ORM with async support
- **PostgreSQL** - Database
- **Redis** - Cache and message broker
- **Celery** - Background task processing
- **Alembic** - Database migrations

## Project Structure

```
backend/
├── app/
│   ├── api/              # API routes
│   │   ├── auth.py       # Authentication endpoints
│   │   ├── conversations.py
│   │   ├── messages.py
│   │   └── webhooks.py   # WhatsApp & Chat App webhooks
│   ├── core/             # Core configuration
│   │   ├── config.py     # Settings
│   │   └── security.py   # JWT & password hashing
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   ├── workers/          # Celery tasks
│   ├── integrations/     # External API adapters
│   ├── database.py       # DB connection
│   └── main.py           # FastAPI app
├── alembic/              # Database migrations
├── tests/                # Tests
├── requirements.txt      # Dependencies
├── .env.example          # Environment variables template
└── Dockerfile
```

## Quick Start

### 1. Prerequisites

- Python 3.11+
- Docker & Docker Compose (recommended)
- PostgreSQL 15+ (if not using Docker)
- Redis 7+ (if not using Docker)

### 2. Setup with Docker (Recommended)

```bash
# Clone repository
cd MAX

# Copy environment file
cp backend/.env.example backend/.env

# Edit .env with your configuration
# At minimum, set SECRET_KEY to a random string

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f backend

# Access API
# http://localhost:8000
# API docs: http://localhost:8000/docs
```

### 3. Setup without Docker

```bash
# Create virtual environment
cd backend
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your configuration

# Start PostgreSQL and Redis locally

# Run database migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload

# In another terminal, start Celery worker
celery -A app.workers.celery_app worker --loglevel=info
```

## API Endpoints

### Health Check
- `GET /` - Root endpoint
- `GET /health` - Health check

### Authentication
- `POST /api/v1/auth/login` - Login (returns JWT token)
- `POST /api/v1/auth/logout` - Logout
- `GET /api/v1/auth/me` - Get current user

### Conversations
- `GET /api/v1/conversations` - List conversations
- `GET /api/v1/conversations/{id}` - Get conversation
- `POST /api/v1/conversations/{id}/assign` - Assign to agent
- `POST /api/v1/conversations/{id}/close` - Close conversation

### Messages
- `GET /api/v1/messages/conversations/{id}/messages` - Get messages
- `POST /api/v1/messages/conversations/{id}/messages` - Send message

### Webhooks
- `GET /api/v1/webhooks/whatsapp` - WhatsApp webhook verification
- `POST /api/v1/webhooks/whatsapp` - WhatsApp webhook
- `POST /api/v1/webhooks/chat-app` - Chat App webhook

## API Documentation

Interactive API documentation available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_auth.py
```

## Development

### Code Quality

```bash
# Format code
black app/

# Sort imports
isort app/

# Lint
flake8 app/

# Type checking
mypy app/
```

### Environment Variables

Key environment variables (see `.env.example` for complete list):

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - JWT secret key (generate with `openssl rand -hex 32`)
- `WHATSAPP_ACCESS_TOKEN` - WhatsApp Cloud API token
- `WHATSAPP_WEBHOOK_VERIFY_TOKEN` - Webhook verification token

## Deployment

### Google Cloud Run

```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/max-backend

# Deploy
gcloud run deploy max-backend \
  --image gcr.io/PROJECT_ID/max-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Environment Setup

For production:
1. Use managed PostgreSQL (Cloud SQL, Supabase)
2. Use managed Redis (Upstash, Memorystore)
3. Set strong `SECRET_KEY`
4. Configure proper CORS origins
5. Enable HTTPS only
6. Set up monitoring and logging

## Monitoring

- **Flower**: Celery monitoring at http://localhost:5555
- **Logs**: `docker-compose logs -f backend`
- **Metrics**: Prometheus metrics at `/metrics` (TODO)

## Troubleshooting

### Database connection errors
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres
```

### Redis connection errors
```bash
# Check Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping
```

### Import errors
```bash
# Rebuild containers
docker-compose build --no-cache
docker-compose up -d
```

## Next Steps

1. ✅ Project structure created
2. ⏭️ Implement database models (see `/docs/02-data-model.md`)
3. ⏭️ Create Alembic migrations
4. ⏭️ Implement authentication with real user model
5. ⏭️ Implement WhatsApp webhook processing
6. ⏭️ Add Celery tasks for triage flow
7. ⏭️ Build frontend UI

## Documentation

See `/docs` folder for complete architecture documentation:
- Architecture overview
- Data model
- API contracts
- Integration patterns
- Deployment guide

## License

Internal use only.
