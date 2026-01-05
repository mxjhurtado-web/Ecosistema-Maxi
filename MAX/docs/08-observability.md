# I. Observability

## Overview

Comprehensive observability strategy covering:
- **Logging**: Structured logs for debugging and audit
- **Metrics**: Performance and business KPIs
- **Tracing**: Request flow across components
- **Alerting**: Proactive issue detection

---

## 1. Logging

### Structured Logging

**Format**: JSON for machine parsing

**Example**:
```json
{
  "timestamp": "2026-01-05T12:00:00.123Z",
  "level": "INFO",
  "service": "core-api",
  "event": "conversation_assigned",
  "conversation_id": "uuid",
  "assigned_to": "agent_uuid",
  "team_id": "sales_uuid",
  "duration_ms": 45,
  "user_id": "supervisor_uuid"
}
```

### Log Levels

| Level | Usage | Examples |
|-------|-------|----------|
| DEBUG | Development only | SQL queries, cache hits |
| INFO | Normal operations | Conversation created, message sent |
| WARNING | Recoverable issues | Rate limit approached, slow query |
| ERROR | Failures | Integration timeout, validation error |
| CRITICAL | System failures | Database down, service crash |

### Key Events to Log

**Conversations**:
- `conversation.created`
- `conversation.assigned`
- `conversation.transferred`
- `conversation.closed`
- `conversation.reopened`

**Messages**:
- `message.received`
- `message.sent`
- `message.delivered`
- `message.failed`

**Integrations**:
- `integration.request`
- `integration.success`
- `integration.failure`
- `integration.timeout`

**AI Tools**:
- `ai.tool_called`
- `ai.tool_success`
- `ai.tool_denied`
- `ai.confirmation_required`

**Auth**:
- `auth.login`
- `auth.logout`
- `auth.permission_denied`

### PII Redaction

**Never log**:
- Customer phone numbers (use hashed ID)
- Message content (log length only)
- API keys/tokens
- Passwords

**Implementation**:
```python
import logging
import json

class PIIRedactingFormatter(logging.Formatter):
    def format(self, record):
        # Redact sensitive fields
        if hasattr(record, 'phone'):
            record.phone = '***REDACTED***'
        if hasattr(record, 'message_content'):
            record.message_content = f"<{len(record.message_content)} chars>"
        return super().format(record)

# Configure logger
handler = logging.StreamHandler()
handler.setFormatter(PIIRedactingFormatter())
logger.addHandler(handler)
```

---

## 2. Metrics

### Technical Metrics

**API Performance**:
- Request rate (requests/sec)
- Response time (p50, p95, p99)
- Error rate (%)
- Active connections

**Database**:
- Query latency
- Connection pool usage
- Slow queries (> 1s)
- Deadlocks

**Workers (Celery)**:
- Queue length
- Task execution time
- Failed tasks
- Worker utilization

**WebSockets**:
- Active connections
- Message throughput
- Connection errors
- Reconnection rate

**Integrations**:
- Request latency per adapter
- Error rate per adapter
- Circuit breaker state
- Cache hit rate

### Business Metrics

**Conversations**:
- New conversations/hour
- Active conversations
- Queue backlog per team
- Conversations closed/hour

**Response Times**:
- First Response Time (FRT): p50, p95, p99
- Resolution Time: p50, p95, p99
- Time in queue: p50, p95, p99

**Agent Performance**:
- Active conversations per agent
- Messages sent per agent
- Avg FRT per agent
- Utilization rate (%)

**Customer Satisfaction**:
- CSAT score (future)
- Conversation ratings (future)

### Prometheus Metrics

**Example Definitions**:
```python
from prometheus_client import Counter, Histogram, Gauge

# Conversations
conversations_total = Counter(
    'conversations_total',
    'Total conversations created',
    ['channel', 'team']
)

conversations_active = Gauge(
    'conversations_active',
    'Currently active conversations',
    ['team', 'status']
)

# Response times
frt_seconds = Histogram(
    'first_response_time_seconds',
    'First response time',
    ['team'],
    buckets=[30, 60, 120, 300, 600, 1800, 3600]
)

# Messages
messages_total = Counter(
    'messages_total',
    'Total messages',
    ['direction', 'channel', 'status']
)

# Integrations
integration_requests_total = Counter(
    'integration_requests_total',
    'Integration requests',
    ['adapter', 'operation', 'status']
)

integration_latency_seconds = Histogram(
    'integration_latency_seconds',
    'Integration request latency',
    ['adapter', 'operation']
)
```

**Usage**:
```python
# Increment counter
conversations_total.labels(channel='whatsapp', team='sales').inc()

# Observe histogram
frt_seconds.labels(team='sales').observe(120.5)

# Set gauge
conversations_active.labels(team='sales', status='queued').set(12)
```

---

## 3. Tracing

### Distributed Tracing

**Tool**: OpenTelemetry

**Trace Flow**:
```
Inbound Message
  ├─ Webhook Validation (5ms)
  ├─ Message Normalization (10ms)
  ├─ Conversation Lookup (25ms)
  │   └─ Database Query (20ms)
  ├─ Save Message (30ms)
  ├─ Trigger Triage Worker (5ms)
  └─ WebSocket Push (15ms)
Total: 90ms
```

**Implementation**:
```python
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Initialize tracer
tracer = trace.get_tracer(__name__)

# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

# Manual span
@app.post("/messages")
async def create_message(data: MessageCreate):
    with tracer.start_as_current_span("create_message") as span:
        span.set_attribute("conversation_id", data.conversation_id)
        span.set_attribute("channel", data.channel)
        
        # Business logic
        message = await save_message(data)
        
        span.set_attribute("message_id", message.id)
        return message
```

### Trace Context Propagation

**Conversation ID as Trace ID**:
```python
# Attach conversation_id to all logs/traces
import contextvars

conversation_context = contextvars.ContextVar('conversation_id')

@app.middleware("http")
async def add_conversation_context(request: Request, call_next):
    conversation_id = request.headers.get('X-Conversation-ID')
    if conversation_id:
        conversation_context.set(conversation_id)
    
    response = await call_next(request)
    return response

# Use in logs
logger.info(
    "message_sent",
    conversation_id=conversation_context.get(None)
)
```

---

## 4. Dashboards

### Grafana Dashboards

#### 1. Operations Dashboard

**Panels**:
- Active conversations (gauge)
- Queue backlog per team (bar chart)
- Messages/hour (time series)
- FRT p95 (time series)
- Error rate (time series)

**Queries**:
```promql
# Active conversations
sum(conversations_active{status="assigned"}) by (team)

# Queue backlog
sum(conversations_active{status="queued"}) by (team)

# FRT p95
histogram_quantile(0.95, rate(first_response_time_seconds_bucket[5m]))
```

#### 2. Team Performance Dashboard

**Panels**:
- Conversations handled (counter)
- Avg FRT by team (gauge)
- Avg resolution time (gauge)
- Agent utilization (heatmap)

#### 3. Integration Health Dashboard

**Panels**:
- Request rate per adapter (time series)
- Error rate per adapter (time series)
- Latency p95 per adapter (time series)
- Circuit breaker state (status panel)

---

## 5. Alerting

### Alert Rules

#### Critical Alerts (PagerDuty)

**Database Down**:
```yaml
alert: DatabaseDown
expr: up{job="postgresql"} == 0
for: 1m
severity: critical
message: "PostgreSQL database is down"
```

**High Error Rate**:
```yaml
alert: HighErrorRate
expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
for: 5m
severity: critical
message: "Error rate > 5% for 5 minutes"
```

**Integration Failure**:
```yaml
alert: IntegrationDown
expr: rate(integration_requests_total{status="failed"}[5m]) > 0.5
for: 10m
severity: critical
message: "Integration {{ $labels.adapter }} failing > 50%"
```

#### Warning Alerts (Slack)

**Queue Backlog**:
```yaml
alert: QueueBacklog
expr: conversations_active{status="queued"} > 20
for: 15m
severity: warning
message: "{{ $labels.team }} queue has {{ $value }} conversations"
```

**Slow FRT**:
```yaml
alert: SlowFRT
expr: histogram_quantile(0.95, rate(first_response_time_seconds_bucket[10m])) > 600
for: 15m
severity: warning
message: "FRT p95 > 10 minutes for {{ $labels.team }}"
```

**High Agent Load**:
```yaml
alert: HighAgentLoad
expr: avg(agent_active_conversations) by (agent_id) > 8
for: 30m
severity: warning
message: "Agent {{ $labels.agent_id }} has {{ $value }} active conversations"
```

---

## 6. Log Aggregation

### ELK Stack (Elasticsearch, Logstash, Kibana)

**Log Pipeline**:
```
Application → Logstash → Elasticsearch → Kibana
```

**Logstash Config**:
```ruby
input {
  file {
    path => "/var/log/max/*.log"
    codec => json
  }
}

filter {
  # Parse timestamp
  date {
    match => ["timestamp", "ISO8601"]
  }
  
  # Add tags
  if [event] == "conversation.created" {
    mutate { add_tag => ["conversation"] }
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "max-logs-%{+YYYY.MM.dd}"
  }
}
```

**Kibana Queries**:
```
# All errors in last hour
level:ERROR AND @timestamp:[now-1h TO now]

# Conversation timeline
conversation_id:"uuid" | sort @timestamp

# Failed integrations
event:integration.failure | stats count by adapter
```

---

## 7. Health Checks

### Endpoints

#### GET /health
Basic liveness check.

**Response** (200):
```json
{
  "status": "healthy",
  "timestamp": "2026-01-05T12:00:00Z"
}
```

#### GET /health/ready
Readiness check (dependencies).

**Response** (200):
```json
{
  "status": "ready",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "celery": "healthy"
  }
}
```

**Response** (503) if any dependency fails:
```json
{
  "status": "not_ready",
  "checks": {
    "database": "healthy",
    "redis": "unhealthy",
    "celery": "healthy"
  }
}
```

---

## 8. Performance Monitoring

### APM (Application Performance Monitoring)

**Tool**: New Relic / Datadog

**Tracked**:
- Endpoint latency breakdown
- Database query performance
- External API calls
- Memory/CPU usage
- Error traces with stack traces

### Slow Query Logging

**PostgreSQL Config**:
```sql
-- Log queries > 1 second
ALTER SYSTEM SET log_min_duration_statement = 1000;

-- Log query plans
ALTER SYSTEM SET auto_explain.log_min_duration = 1000;
```

**Review**:
```sql
-- Find slow queries
SELECT 
  query,
  calls,
  mean_exec_time,
  max_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 1000
ORDER BY mean_exec_time DESC
LIMIT 20;
```

---

## 9. Audit Trail

### Compliance Logging

**Requirements**:
- Immutable logs (append-only)
- Retention: 1 year minimum
- Searchable by conversation/user/date

**Storage**: Separate audit database or S3

**Events**:
- All conversation state changes
- All permission checks (granted/denied)
- All AI tool invocations
- All integration calls
- All user logins/logouts

**Example Query**:
```sql
-- Get full audit trail for conversation
SELECT 
  event_type,
  actor_type,
  actor_id,
  old_value,
  new_value,
  created_at
FROM conversation_events
WHERE conversation_id = 'uuid'
ORDER BY created_at;
```

---

**Next**: See [Roadmap](./09-roadmap.md) for implementation phases.
