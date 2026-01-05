# C. Data Model

## Database: PostgreSQL 14+

### Schema Overview

```
users ──┬─── team_memberships ─── teams ──┬─── business_hours
        │                                  └─── sla_policies
        ├─── agent_presence
        ├─── agent_stats
        └─── agent_skills

customers ──┬─── customer_identities
            └─── conversations ──┬─── messages ──┬─── media_files
                                 │               └─── (content)
                                 ├─── conversation_events
                                 ├─── conversation_tags ─── tags
                                 ├─── conversation_notes
                                 ├─── sla_violations
                                 └─── conversation_assignments

internal_threads ─── internal_messages ─── internal_thread_members

integrations ─── integration_logs
              └─── ai_tool_audit_logs

whatsapp_templates
canned_responses
webhook_subscriptions ─── webhook_deliveries
rate_limit_buckets
```


---

## Core Tables

### `users`
Agent and admin accounts.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'supervisor', 'team_lead', 'agent')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = TRUE;
```

**Fields**:
- `role`: admin | supervisor | team_lead | agent
- `is_active`: Soft delete flag

---

### `teams`
Sales, Support, Customer Service.

```sql
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_teams_slug ON teams(slug);
```

**Initial Data**:
```sql
INSERT INTO teams (name, slug) VALUES
    ('Sales', 'sales'),
    ('Support', 'support'),
    ('Customer Service', 'customer_service');
```

---

### `team_memberships`
Many-to-many: users ↔ teams.

```sql
CREATE TABLE team_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, team_id)
);

CREATE INDEX idx_team_memberships_user ON team_memberships(user_id);
CREATE INDEX idx_team_memberships_team ON team_memberships(team_id);
```

---

### `customers`
End-users from WhatsApp or Chat App.

```sql
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id VARCHAR(255) UNIQUE NOT NULL, -- phone number or customer_id
    channel VARCHAR(50) NOT NULL CHECK (channel IN ('whatsapp', 'chat_app')),
    name VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_customers_external_id ON customers(external_id);
CREATE INDEX idx_customers_channel ON customers(channel);
CREATE INDEX idx_customers_metadata ON customers USING GIN(metadata);
```

**Fields**:
- `external_id`: WhatsApp phone (+1234567890) or chat app customer_id
- `metadata`: Custom fields (language, timezone, etc.)

---

### `conversations`
Core conversation entity.

```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    channel VARCHAR(50) NOT NULL CHECK (channel IN ('whatsapp', 'chat_app')),
    team_id UUID REFERENCES teams(id) ON DELETE SET NULL,
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'new' CHECK (status IN (
        'new', 'triage', 'queued', 'assigned', 
        'pending_customer', 'pending_agent', 'closed'
    )),
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    first_message_at TIMESTAMPTZ,
    first_response_at TIMESTAMPTZ,
    assigned_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    closed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    close_reason VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_conversations_customer ON conversations(customer_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_team ON conversations(team_id);
CREATE INDEX idx_conversations_assigned ON conversations(assigned_to);
CREATE INDEX idx_conversations_created ON conversations(created_at DESC);
CREATE INDEX idx_conversations_queue ON conversations(team_id, status) 
    WHERE status IN ('queued', 'triage');
```

**Key Indexes**:
- `idx_conversations_queue`: Fast queue queries per team
- `idx_conversations_created`: Recent conversations

**Computed Metrics** (via triggers or app logic):
- FRT = `first_response_at - first_message_at`
- Resolution Time = `closed_at - first_message_at`

---

### `messages`
All messages (customer ↔ agent).

```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    channel_message_id VARCHAR(255), -- External ID from WhatsApp/Chat App
    direction VARCHAR(20) NOT NULL CHECK (direction IN ('inbound', 'outbound')),
    sender_type VARCHAR(20) NOT NULL CHECK (sender_type IN ('customer', 'agent', 'system')),
    sender_id UUID, -- user_id if agent, customer_id if customer
    content_type VARCHAR(50) NOT NULL DEFAULT 'text',
    content_text TEXT,
    content_media_url TEXT,
    content_metadata JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'sent' CHECK (status IN ('pending', 'sent', 'delivered', 'read', 'failed')),
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    delivered_at TIMESTAMPTZ,
    read_at TIMESTAMPTZ,
    failed_reason TEXT,
    retry_count INT DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_messages_channel_id ON messages(channel_message_id) 
    WHERE channel_message_id IS NOT NULL;
CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at DESC);
CREATE INDEX idx_messages_status ON messages(status) WHERE status IN ('pending', 'failed');
```

**Deduplication**: `channel_message_id` ensures no duplicate webhook processing.

**Example**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "conversation_id": "...",
  "channel_message_id": "wamid.HBgNMTIzNDU2Nzg5MAA=",
  "direction": "inbound",
  "sender_type": "customer",
  "content_type": "text",
  "content_text": "Hello, I need help",
  "status": "delivered",
  "sent_at": "2026-01-05T12:00:00Z"
}
```

---

### `conversation_events`
Audit trail for state changes.

```sql
CREATE TABLE conversation_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    actor_type VARCHAR(20) CHECK (actor_type IN ('user', 'system', 'ai')),
    actor_id UUID, -- user_id or null for system
    old_value JSONB,
    new_value JSONB,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_events_conversation ON conversation_events(conversation_id, created_at DESC);
CREATE INDEX idx_events_type ON conversation_events(event_type);
CREATE INDEX idx_events_actor ON conversation_events(actor_id) WHERE actor_id IS NOT NULL;
```

**Event Types**:
- `conversation.created`
- `conversation.assigned` (old: null, new: user_id)
- `conversation.transferred` (old: user_id_1, new: user_id_2)
- `conversation.closed` (metadata: close_reason)
- `conversation.reopened`
- `triage.completed` (metadata: routing_decision)
- `ai.tool_called` (metadata: tool_name, params)

**Example**:
```json
{
  "event_type": "conversation.assigned",
  "actor_type": "user",
  "actor_id": "supervisor-uuid",
  "old_value": null,
  "new_value": {"assigned_to": "agent-uuid", "team_id": "sales-uuid"},
  "metadata": {"assignment_method": "manual"}
}
```

---

### `tags`
Reusable labels.

```sql
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    color VARCHAR(7) DEFAULT '#3B82F6',
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE, -- null = global
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tags_team ON tags(team_id);
```

---

### `conversation_tags`
Many-to-many: conversations ↔ tags.

```sql
CREATE TABLE conversation_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    added_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(conversation_id, tag_id)
);

CREATE INDEX idx_conversation_tags_conv ON conversation_tags(conversation_id);
CREATE INDEX idx_conversation_tags_tag ON conversation_tags(tag_id);
```

---

### `conversation_notes`
Internal agent notes.

```sql
CREATE TABLE conversation_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    is_pinned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_notes_conversation ON conversation_notes(conversation_id, created_at DESC);
CREATE INDEX idx_notes_pinned ON conversation_notes(conversation_id) WHERE is_pinned = TRUE;
```

---

## Internal Chat Tables

### `internal_threads`
Agent-to-agent chat threads.

```sql
CREATE TABLE internal_threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255),
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    is_archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_internal_threads_created ON internal_threads(created_at DESC);
CREATE INDEX idx_internal_threads_active ON internal_threads(is_archived) WHERE is_archived = FALSE;
```

---

### `internal_thread_members`
Thread participants.

```sql
CREATE TABLE internal_thread_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id UUID NOT NULL REFERENCES internal_threads(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    last_read_at TIMESTAMPTZ,
    UNIQUE(thread_id, user_id)
);

CREATE INDEX idx_thread_members_user ON internal_thread_members(user_id);
CREATE INDEX idx_thread_members_thread ON internal_thread_members(thread_id);
```

---

### `internal_messages`
Messages within threads.

```sql
CREATE TABLE internal_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id UUID NOT NULL REFERENCES internal_threads(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_internal_messages_thread ON internal_messages(thread_id, created_at DESC);
```

---

## Integration Tables

### `integration_configs`
External system credentials (encrypted).

```sql
CREATE TABLE integration_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL, -- 'ticketing', 'transaction_status', 'transaction_create'
    type VARCHAR(50) NOT NULL, -- 'api_key', 'oauth2'
    credentials_encrypted BYTEA NOT NULL, -- Encrypted JSON
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Security**: Use `pgcrypto` or app-level encryption (e.g., Fernet).

---

### `integration_logs`
Audit trail for external API calls.

```sql
CREATE TABLE integration_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    integration_name VARCHAR(100) NOT NULL,
    operation VARCHAR(100) NOT NULL,
    request_payload JSONB,
    response_payload JSONB,
    status_code INT,
    duration_ms INT,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_integration_logs_name ON integration_logs(integration_name, created_at DESC);
CREATE INDEX idx_integration_logs_error ON integration_logs(integration_name) WHERE error IS NOT NULL;
```

---

### `ai_tool_audit_logs`
AI agent tool invocations.

```sql
CREATE TABLE ai_tool_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    tool_name VARCHAR(100) NOT NULL,
    input_params JSONB NOT NULL,
    output_result JSONB,
    status VARCHAR(50) NOT NULL CHECK (status IN ('success', 'failed', 'denied')),
    denial_reason TEXT,
    executed_by VARCHAR(50) DEFAULT 'ai_agent',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ai_tool_logs_conversation ON ai_tool_audit_logs(conversation_id, created_at DESC);
CREATE INDEX idx_ai_tool_logs_tool ON ai_tool_audit_logs(tool_name);
CREATE INDEX idx_ai_tool_logs_denied ON ai_tool_audit_logs(status) WHERE status = 'denied';
```

**Example**:
```json
{
  "tool_name": "create_transaction_draft",
  "input_params": {
    "customer_id": "uuid",
    "amount": 500.00,
    "description": "Product purchase"
  },
  "output_result": {
    "draft_id": "draft_123",
    "status": "pending_confirmation"
  },
  "status": "success"
}
```

---

## Metrics Tables

### `agent_stats`
Daily agent performance.

```sql
CREATE TABLE agent_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    conversations_handled INT DEFAULT 0,
    messages_sent INT DEFAULT 0,
    avg_frt_seconds INT,
    avg_resolution_seconds INT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, date)
);

CREATE INDEX idx_agent_stats_user_date ON agent_stats(user_id, date DESC);
```

---

### `team_stats`
Daily team performance.

```sql
CREATE TABLE team_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    conversations_created INT DEFAULT 0,
    conversations_closed INT DEFAULT 0,
    avg_frt_seconds INT,
    avg_resolution_seconds INT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(team_id, date)
);

CREATE INDEX idx_team_stats_team_date ON team_stats(team_id, date DESC);
```

---

## Materialized Views (Optional)

### `queue_summary`
Real-time queue counts.

```sql
CREATE MATERIALIZED VIEW queue_summary AS
SELECT 
    team_id,
    status,
    COUNT(*) as count,
    MAX(created_at) as oldest_conversation
FROM conversations
WHERE status IN ('queued', 'triage')
GROUP BY team_id, status;

CREATE UNIQUE INDEX idx_queue_summary ON queue_summary(team_id, status);
```

**Refresh**: Via trigger or periodic job (every 30s).

---

## Enhancement Tables

### `media_files`
Store media files from WhatsApp/Chat App.

```sql
CREATE TABLE media_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    channel_media_id VARCHAR(255), -- WhatsApp media ID
    media_type VARCHAR(50) NOT NULL CHECK (media_type IN ('image', 'video', 'audio', 'document')),
    mime_type VARCHAR(100),
    file_size_bytes BIGINT,
    original_filename VARCHAR(255),
    storage_url TEXT NOT NULL, -- S3/CloudFlare R2 URL
    storage_key VARCHAR(500), -- S3 key for deletion
    thumbnail_url TEXT,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_media_files_message ON media_files(message_id);
CREATE INDEX idx_media_files_expires ON media_files(expires_at) WHERE expires_at IS NOT NULL;
```

**Fields**:
- `channel_media_id`: WhatsApp's media ID for download
- `storage_url`: Signed URL for agent access (expires in 7 days)
- `storage_key`: S3 key for permanent storage

---

### `customer_identities`
Link multiple identities to same customer.

```sql
CREATE TABLE customer_identities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    channel VARCHAR(50) NOT NULL CHECK (channel IN ('whatsapp', 'chat_app', 'email', 'sms')),
    external_id VARCHAR(255) NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMPTZ,
    linked_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(channel, external_id)
);

CREATE INDEX idx_customer_identities_customer ON customer_identities(customer_id);
CREATE INDEX idx_customer_identities_external ON customer_identities(channel, external_id);
CREATE INDEX idx_customer_identities_primary ON customer_identities(customer_id) WHERE is_primary = TRUE;
```

**Usage**:
- Customer uses WhatsApp: +1234567890
- Same customer uses Chat App: customer_abc123
- Agent links both identities
- All conversations appear in unified customer profile

---

### `canned_responses`
Pre-defined quick replies for agents.

```sql
CREATE TABLE canned_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    shortcut VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    language VARCHAR(10) DEFAULT 'es',
    category VARCHAR(100),
    usage_count INT DEFAULT 0,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(team_id, shortcut)
);

CREATE INDEX idx_canned_responses_team ON canned_responses(team_id);
CREATE INDEX idx_canned_responses_shortcut ON canned_responses(shortcut);
CREATE INDEX idx_canned_responses_category ON canned_responses(category);
```

**Example**:
```sql
INSERT INTO canned_responses (team_id, shortcut, title, content) VALUES
    ('sales_uuid', '/greeting', 'Saludo inicial', '¡Hola! Gracias por contactarnos. ¿En qué puedo ayudarte hoy?'),
    ('support_uuid', '/reset_password', 'Reset contraseña', 'Te envío el link para resetear tu contraseña: {link}');
```

---

### `sla_policies`
Service Level Agreement definitions.

```sql
CREATE TABLE sla_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    priority VARCHAR(20) NOT NULL CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    frt_target_seconds INT NOT NULL,
    resolution_target_seconds INT NOT NULL,
    escalation_after_seconds INT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(team_id, priority)
);

CREATE INDEX idx_sla_policies_team ON sla_policies(team_id);
```

**Example**:
```sql
INSERT INTO sla_policies (team_id, priority, frt_target_seconds, resolution_target_seconds, escalation_after_seconds) VALUES
    ('sales_uuid', 'urgent', 180, 900, 600),      -- 3min FRT, 15min resolution, escalate after 10min
    ('sales_uuid', 'high', 300, 1800, 1200),      -- 5min FRT, 30min resolution
    ('sales_uuid', 'normal', 600, 3600, NULL),    -- 10min FRT, 1h resolution
    ('support_uuid', 'urgent', 120, 600, 300);    -- 2min FRT, 10min resolution
```

---

### `sla_violations`
Track SLA breaches.

```sql
CREATE TABLE sla_violations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sla_policy_id UUID NOT NULL REFERENCES sla_policies(id) ON DELETE CASCADE,
    violation_type VARCHAR(50) NOT NULL CHECK (violation_type IN ('frt', 'resolution')),
    target_seconds INT NOT NULL,
    actual_seconds INT NOT NULL,
    escalated_to UUID REFERENCES users(id) ON DELETE SET NULL,
    escalated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sla_violations_conversation ON sla_violations(conversation_id);
CREATE INDEX idx_sla_violations_created ON sla_violations(created_at DESC);
```

---

### `business_hours`
Team operating hours.

```sql
CREATE TABLE business_hours (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    day_of_week INT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6), -- 0=Monday, 6=Sunday
    open_time TIME NOT NULL,
    close_time TIME NOT NULL,
    timezone VARCHAR(50) DEFAULT 'America/Mexico_City',
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(team_id, day_of_week)
);

CREATE INDEX idx_business_hours_team ON business_hours(team_id);
```

**Example**:
```sql
-- Sales team: Monday-Friday 9am-6pm
INSERT INTO business_hours (team_id, day_of_week, open_time, close_time) VALUES
    ('sales_uuid', 0, '09:00', '18:00'),  -- Monday
    ('sales_uuid', 1, '09:00', '18:00'),  -- Tuesday
    ('sales_uuid', 2, '09:00', '18:00'),  -- Wednesday
    ('sales_uuid', 3, '09:00', '18:00'),  -- Thursday
    ('sales_uuid', 4, '09:00', '18:00');  -- Friday
```

---

### `whatsapp_templates`
WhatsApp message templates.

```sql
CREATE TABLE whatsapp_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    language VARCHAR(10) NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN ('MARKETING', 'UTILITY', 'AUTHENTICATION')),
    status VARCHAR(50) NOT NULL CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
    components JSONB NOT NULL,
    whatsapp_template_id VARCHAR(255),
    rejection_reason TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name, language)
);

CREATE INDEX idx_whatsapp_templates_status ON whatsapp_templates(status);
CREATE INDEX idx_whatsapp_templates_name ON whatsapp_templates(name);
```

**Example**:
```json
{
  "name": "follow_up",
  "language": "es",
  "category": "UTILITY",
  "status": "APPROVED",
  "components": [
    {
      "type": "BODY",
      "text": "Hola {{1}}, ¿aún necesitas ayuda con {{2}}?"
    }
  ]
}
```

---

### `agent_skills`
Agent skills for routing.

```sql
CREATE TABLE agent_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill_name VARCHAR(100) NOT NULL,
    proficiency_level INT NOT NULL CHECK (proficiency_level BETWEEN 1 AND 5),
    verified_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, skill_name)
);

CREATE INDEX idx_agent_skills_user ON agent_skills(user_id);
CREATE INDEX idx_agent_skills_skill ON agent_skills(skill_name);
```

**Example Skills**:
- `english` (language)
- `billing` (domain)
- `technical_support` (domain)
- `sales_enterprise` (specialization)

---

### `webhook_subscriptions`
Outbound webhooks for external systems.

```sql
CREATE TABLE webhook_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT NOT NULL,
    events TEXT[] NOT NULL,
    secret VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    retry_count INT DEFAULT 3,
    timeout_seconds INT DEFAULT 10,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_webhook_subscriptions_active ON webhook_subscriptions(is_active) WHERE is_active = TRUE;
```

**Example**:
```sql
INSERT INTO webhook_subscriptions (url, events, secret) VALUES
    ('https://crm.example.com/webhooks/max', 
     ARRAY['conversation.closed', 'conversation.assigned'], 
     'secret_key_123');
```

---

### `webhook_deliveries`
Track webhook delivery attempts.

```sql
CREATE TABLE webhook_deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES webhook_subscriptions(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    status_code INT,
    response_body TEXT,
    error TEXT,
    attempt_number INT DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_webhook_deliveries_subscription ON webhook_deliveries(subscription_id, created_at DESC);
CREATE INDEX idx_webhook_deliveries_failed ON webhook_deliveries(subscription_id) WHERE error IS NOT NULL;
```

---

### `rate_limit_buckets`
Customer-side rate limiting.

```sql
CREATE TABLE rate_limit_buckets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    bucket_type VARCHAR(50) NOT NULL CHECK (bucket_type IN ('message', 'conversation')),
    count INT DEFAULT 0,
    window_start TIMESTAMPTZ NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,
    is_blocked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(customer_id, bucket_type, window_start)
);

CREATE INDEX idx_rate_limit_buckets_customer ON rate_limit_buckets(customer_id);
CREATE INDEX idx_rate_limit_buckets_window ON rate_limit_buckets(window_end) WHERE is_blocked = FALSE;
```

**Usage**:
- Track messages per customer per minute
- Block if > 20 messages/minute
- Auto-unblock after window expires

---

## Data Retention

| Table | Retention | Strategy |
|-------|-----------|----------|
| `messages` | 2 years | Archive to S3, keep metadata |
| `conversation_events` | 1 year | Archive old events |
| `integration_logs` | 90 days | Rotate to cold storage |
| `ai_tool_audit_logs` | 1 year | Compliance requirement |
| `internal_messages` | 1 year | Soft delete |

---

**Next**: See [States & Flows](./03-states-flows.md) for conversation lifecycle.
