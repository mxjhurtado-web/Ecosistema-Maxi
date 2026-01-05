# B. Component Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL CHANNELS                            │
├──────────────────────┬──────────────────────────────────────────────┤
│  WhatsApp Cloud API  │         Chat App (customer_id)               │
└──────────┬───────────┴────────────────┬─────────────────────────────┘
           │                            │
           ▼                            ▼
    ┌─────────────┐            ┌──────────────┐
    │   Ingress   │            │   Ingress    │
    │  WhatsApp   │            │   Chat App   │
    └──────┬──────┘            └──────┬───────┘
           │                          │
           └──────────┬───────────────┘
                      │
                      ▼
              ┌───────────────┐
              │  Message      │◄──── Webhook validation
              │  Normalizer   │      Deduplication
              └───────┬───────┘      Channel abstraction
                      │
                      ▼
              ┌───────────────┐
              │   Core API    │◄──── FastAPI
              │   (FastAPI)   │      Business logic
              └───┬───────┬───┘      State management
                  │       │
        ┌─────────┘       └─────────┐
        │                           │
        ▼                           ▼
┌──────────────┐          ┌──────────────────┐
│   Workers    │          │  Realtime        │
│   (Celery)   │          │  Gateway (WS)    │
├──────────────┤          ├──────────────────┤
│• Triage Flow │          │• Agent UI        │
│• Auto-assign │          │• Live updates    │
│• Metrics     │          │• Typing          │
│• Cleanup     │          │• Presence        │
└──────┬───────┘          └────────┬─────────┘
       │                           │
       │                           │
       ▼                           ▼
┌─────────────────────────────────────────┐
│         PostgreSQL + Redis              │
│  • Conversations  • Messages  • Events  │
│  • Users  • Teams  • Queue state        │
└─────────────────────────────────────────┘

       ┌──────────────────────────────────┐
       │      Integration Layer           │
       ├──────────────────────────────────┤
       │  ┌────────────────────────────┐  │
       │  │   Integration Hub          │  │
       │  ├────────────────────────────┤  │
       │  │ • Ticketing Adapter        │  │
       │  │ • Transaction Status       │  │
       │  │ • Transaction Create       │  │
       │  └────────────────────────────┘  │
       │              ▲                   │
       │              │ Secured calls     │
       │  ┌───────────┴────────────────┐  │
       │  │   AI Tool Gateway          │  │
       │  ├────────────────────────────┤  │
       │  │ • Permission validation    │  │
       │  │ • Rate limiting            │  │
       │  │ • PII redaction            │  │
       │  │ • Audit logging            │  │
       │  │ • Draft/Commit flow        │  │
       │  └────────────────────────────┘  │
       │              ▲                   │
       └──────────────┼───────────────────┘
                      │
                      │
              ┌───────┴────────┐
              │   AI Agent     │
              │   (Future)     │
              └────────────────┘
```

## Component Details

### 1. Ingress Layer

#### WhatsApp Ingress
- **Purpose**: Receive webhooks from WhatsApp Cloud API
- **Responsibilities**:
  - Webhook signature verification
  - Handle message types (text, media, interactive)
  - Track delivery statuses (sent/delivered/read/failed)
  - Manage 24-hour window constraints
  - Retry failed sends with exponential backoff
- **Tech**: FastAPI endpoint + Celery for async sends
- **Key Challenge**: Idempotency via `channel_message_id` deduplication

#### Chat App Ingress
- **Purpose**: Receive messages from proprietary chat app
- **Responsibilities**:
  - Authenticate requests (API key or JWT)
  - Map `customer_id` to internal customer record
  - Real-time message delivery
- **Tech**: FastAPI endpoint + WebSocket for bidirectional
- **Key Challenge**: Maintain customer identity across sessions

### 2. Message Normalizer

**Purpose**: Abstract channel differences into unified message format

**Normalized Message Schema**:
```json
{
  "message_id": "uuid",
  "conversation_id": "uuid",
  "channel": "whatsapp|chat_app",
  "channel_message_id": "unique-per-channel",
  "direction": "inbound|outbound",
  "sender": {
    "type": "customer|agent|system",
    "id": "uuid",
    "name": "string"
  },
  "content": {
    "type": "text|image|video|audio|document|interactive",
    "text": "message body",
    "media_url": "https://...",
    "metadata": {}
  },
  "timestamp": "2026-01-05T12:00:00Z",
  "status": "sent|delivered|read|failed",
  "metadata": {
    "whatsapp_status": "...",
    "retry_count": 0
  }
}
```

### 3. Core API (FastAPI)

**Purpose**: Central business logic and state management

**Modules**:
- **Auth**: JWT-based authentication, session management
- **Users & Teams**: RBAC, team membership, role assignment
- **Conversations**: CRUD, state transitions, assignment logic
- **Messages**: Send/receive, threading, search
- **Tags & Notes**: Metadata, internal annotations
- **Internal Chat**: Agent-to-agent messaging (separate DB tables)
- **Reporting**: Metrics aggregation, export

**Database**: PostgreSQL with connection pooling
**Cache**: Redis for session, queue state, rate limits

### 4. Workers (Celery)

**Purpose**: Async background processing

**Tasks**:
1. **Triage Flow Executor**: Run conversation routing logic
2. **Auto-Assignment** (Phase 2): Capacity-based agent assignment
3. **Metrics Calculator**: Compute FRT, resolution time, SLA compliance
4. **Cleanup Jobs**: Archive old conversations, purge temp data
5. **Integration Sync**: Poll external systems for updates
6. **Notification Dispatcher**: Email/Slack alerts for supervisors

**Queue Structure**:
- `high`: Real-time triage, message sends
- `default`: Metrics, assignments
- `low`: Cleanup, archival

### 5. Realtime Gateway (WebSockets)

**Purpose**: Push updates to agent UI

**Events**:
- `conversation.new`: New conversation in queue
- `conversation.assigned`: Conversation assigned to agent
- `message.received`: New customer message
- `message.sent`: Agent message delivered
- `agent.typing`: Typing indicators
- `agent.presence`: Online/away/offline status
- `queue.updated`: Queue count changes

**Tech**: FastAPI WebSocket + Redis Pub/Sub for horizontal scaling

**Connection Auth**: JWT token in WS handshake

### 6. Integration Hub

**Purpose**: Centralized adapter layer for external systems

**Adapters**:

#### Ticketing Adapter
- **Operations**: `create_ticket`, `get_ticket_status`, `add_comment`
- **Auth**: API Key (stored in secrets manager)
- **Timeout**: 10s
- **Retry**: 3 attempts with exponential backoff
- **Cache**: Ticket status cached 5 minutes

#### Transaction Status Adapter
- **Operations**: `get_transaction_status`, `get_transaction_history`
- **Auth**: OAuth2 client credentials
- **Timeout**: 5s
- **Cache**: Status cached 2 minutes (invalidate on webhook)

#### Transaction Create Adapter
- **Operations**: `create_draft_transaction`, `commit_transaction`, `cancel_draft`
- **Auth**: OAuth2 + HMAC signature
- **Timeout**: 15s (commit), 5s (draft)
- **Idempotency**: `idempotency_key` header

**Error Handling**:
- Failed calls → Dead Letter Queue (DLQ)
- Supervisor notification on repeated failures
- Circuit breaker pattern (5 failures → open for 60s)

### 7. AI Tool Gateway

**Purpose**: Security layer between AI agents and integrations

**Architecture**:
```
AI Agent → Tool Request → Gateway → Validation → Integration Hub → External API
                              ↓
                         Audit Log
```

**Responsibilities**:
1. **Permission Validation**: Check if tool allowed for current conversation context
2. **Input Sanitization**: Allowlist fields, reject suspicious patterns
3. **Rate Limiting**: Max 10 tool calls per conversation per hour
4. **PII Redaction**: Remove sensitive data from logs
5. **Audit Trail**: Log every tool invocation with conversation_id
6. **Draft/Commit Flow**: Two-phase transactions for creates

**Tool Definitions**:
- `search_tickets(customer_id, status)`
- `get_transaction_status(transaction_id)`
- `create_transaction_draft(customer_id, amount, description)`
- `commit_transaction(draft_id, confirmation_token)`

**Security Rules**:
- AI never receives API keys/tokens
- All calls proxied through gateway
- Confirmation tokens required for financial transactions
- Human-in-loop for amounts > $1000

### 8. Reporting & Analytics

**Purpose**: Operational dashboards and metrics

**Metrics**:
- **FRT (First Response Time)**: P50, P95, P99 by team
- **Resolution Time**: Average, median by team
- **Queue Backlog**: Real-time count per team
- **Agent Utilization**: Active conversations per agent
- **CSAT**: Customer satisfaction scores (future)

**Storage**: TimescaleDB extension on PostgreSQL for time-series data

**Dashboards**: Grafana or internal React dashboard

## Data Flow Examples

### Inbound WhatsApp Message
```
1. WhatsApp → Webhook → Ingress validates signature
2. Ingress → Message Normalizer → Dedupe check (channel_message_id)
3. Normalizer → Core API → Find/create conversation
4. Core API → Save message to DB
5. Core API → Trigger triage worker (if new conversation)
6. Core API → Realtime Gateway → Push to assigned agent WS
7. Triage Worker → Evaluate routing rules → Assign to team queue
8. Realtime Gateway → Notify team supervisors
```

### Agent Sends Reply
```
1. Agent UI → Core API (POST /messages)
2. Core API → Validate 24h window (WhatsApp)
3. Core API → Save message to DB (status: pending)
4. Core API → Queue send task (Celery)
5. Worker → Call WhatsApp API
6. Worker → Update message status (sent)
7. Realtime Gateway → Push status update to agent
8. WhatsApp webhook → Delivery status → Update DB
```

### AI Tool Call (Create Transaction)
```
1. AI Agent → AI Tool Gateway (create_transaction_draft)
2. Gateway → Validate permissions (sales team only)
3. Gateway → Rate limit check
4. Gateway → Integration Hub → Transaction Create Adapter
5. Adapter → External API (create draft)
6. Adapter → Return draft_id
7. Gateway → Audit log
8. AI → Ask customer for confirmation
9. Customer → "Yes, proceed"
10. AI → Gateway (commit_transaction with confirmation_token)
11. Gateway → Validate token
12. Gateway → Integration Hub → Commit draft
13. Adapter → External API (finalize transaction)
14. Gateway → Audit log (committed)
```

## Technology Decisions & Tradeoffs

| Decision | Rationale | Tradeoff |
|----------|-----------|----------|
| FastAPI | Modern, async, auto docs | Less mature than Django |
| PostgreSQL | ACID, JSON support, proven | Horizontal scaling harder than NoSQL |
| Celery | Mature, Python-native | Complex setup, needs Redis/RabbitMQ |
| WebSockets | Real-time, bidirectional | Stateful, harder to scale |
| Redis | Fast, pub/sub, caching | In-memory, needs persistence config |
| Monolith (Phase 1) | Faster development | Harder to scale components independently |

## Scalability Considerations

**Current Scale** (300-500 msg/day):
- Single server handles easily
- PostgreSQL on modest instance
- Redis on same server

**Future Scale** (5000+ msg/day):
- Horizontal API scaling (load balancer)
- Read replicas for PostgreSQL
- Redis cluster for cache
- Separate Celery workers by queue priority
- CDN for media files

---

**Next**: See [Data Model](./02-data-model.md) for database schema.
