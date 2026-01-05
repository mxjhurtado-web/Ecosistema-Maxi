# F. API Contract

## Base URL
```
https://api.max.internal/v1
```

## Authentication

All endpoints require JWT token in header:
```
Authorization: Bearer <jwt_token>
```

---

## 1. Authentication

### POST /auth/login
Login and get JWT token.

**Request**:
```json
{
  "email": "agent@example.com",
  "password": "secure_password"
}
```

**Response** (200):
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "dGhpc2lz...",
  "expires_in": 28800,
  "user": {
    "id": "uuid",
    "email": "agent@example.com",
    "full_name": "Maria Garcia",
    "role": "agent",
    "teams": [
      {"id": "uuid", "name": "Sales", "slug": "sales"}
    ]
  }
}
```

---

### POST /auth/refresh
Refresh access token.

**Request**:
```json
{
  "refresh_token": "dGhpc2lz..."
}
```

**Response** (200):
```json
{
  "access_token": "eyJhbGc...",
  "expires_in": 28800
}
```

---

## 2. Users & Teams

### GET /users
List users (Admin/Supervisor only).

**Query Params**:
- `team_id` (optional): Filter by team
- `role` (optional): Filter by role
- `is_active` (optional): true/false

**Response** (200):
```json
{
  "users": [
    {
      "id": "uuid",
      "email": "agent@example.com",
      "full_name": "Maria Garcia",
      "role": "agent",
      "is_active": true,
      "teams": [{"id": "uuid", "name": "Sales"}]
    }
  ],
  "total": 150
}
```

---

### POST /users
Create user (Admin only).

**Request**:
```json
{
  "email": "newagent@example.com",
  "password": "temp_password",
  "full_name": "Juan Perez",
  "role": "agent",
  "team_ids": ["sales_uuid"]
}
```

**Response** (201):
```json
{
  "id": "uuid",
  "email": "newagent@example.com",
  "full_name": "Juan Perez",
  "role": "agent"
}
```

---

### GET /teams
List teams.

**Response** (200):
```json
{
  "teams": [
    {
      "id": "uuid",
      "name": "Sales",
      "slug": "sales",
      "active_agents": 45,
      "queued_conversations": 12
    }
  ]
}
```

---

## 3. Conversations

### GET /conversations
List conversations (scoped by role).

**Query Params**:
- `status`: new|triage|queued|assigned|pending_customer|pending_agent|closed
- `team_id`: Filter by team
- `assigned_to`: Filter by agent
- `channel`: whatsapp|chat_app
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20, max: 100)

**Response** (200):
```json
{
  "conversations": [
    {
      "id": "uuid",
      "customer": {
        "id": "uuid",
        "name": "Juan Lopez",
        "external_id": "+1234567890"
      },
      "channel": "whatsapp",
      "team": {"id": "uuid", "name": "Sales"},
      "assigned_to": {
        "id": "uuid",
        "full_name": "Maria Garcia"
      },
      "status": "assigned",
      "priority": "normal",
      "unread_count": 2,
      "last_message": {
        "content_text": "Gracias por tu ayuda",
        "sent_at": "2026-01-05T12:00:00Z",
        "direction": "inbound"
      },
      "created_at": "2026-01-05T11:30:00Z",
      "updated_at": "2026-01-05T12:00:00Z"
    }
  ],
  "total": 45,
  "page": 1,
  "pages": 3
}
```

---

### GET /conversations/{id}
Get conversation details.

**Response** (200):
```json
{
  "id": "uuid",
  "customer": {
    "id": "uuid",
    "name": "Juan Lopez",
    "external_id": "+1234567890",
    "metadata": {"language": "es"}
  },
  "channel": "whatsapp",
  "team": {"id": "uuid", "name": "Sales"},
  "assigned_to": {"id": "uuid", "full_name": "Maria Garcia"},
  "status": "assigned",
  "priority": "normal",
  "first_message_at": "2026-01-05T11:30:00Z",
  "first_response_at": "2026-01-05T11:32:00Z",
  "assigned_at": "2026-01-05T11:31:00Z",
  "tags": [
    {"id": "uuid", "name": "VIP", "color": "#FF0000"}
  ],
  "metadata": {
    "triage_responses": ["1", "Quiero comprar"],
    "product_interest": "plan premium"
  },
  "created_at": "2026-01-05T11:30:00Z",
  "updated_at": "2026-01-05T12:00:00Z"
}
```

---

### POST /conversations/{id}/assign
Assign conversation to agent.

**Request**:
```json
{
  "assigned_to": "agent_uuid"
}
```

**Response** (200):
```json
{
  "id": "uuid",
  "assigned_to": {"id": "agent_uuid", "full_name": "Maria Garcia"},
  "status": "assigned",
  "assigned_at": "2026-01-05T12:00:00Z"
}
```

---

### POST /conversations/{id}/take
Agent takes conversation from queue.

**Request**: Empty body

**Response** (200):
```json
{
  "id": "uuid",
  "assigned_to": {"id": "current_user_uuid", "full_name": "Maria Garcia"},
  "status": "assigned"
}
```

**Errors**:
- 409: Agent at capacity
- 400: Conversation not in queue

---

### POST /conversations/{id}/transfer
Transfer conversation to another team/agent.

**Request**:
```json
{
  "to_team_id": "support_uuid",
  "to_agent_id": null,
  "reason": "Customer needs technical support"
}
```

**Response** (200):
```json
{
  "id": "uuid",
  "team": {"id": "support_uuid", "name": "Support"},
  "assigned_to": null,
  "status": "queued"
}
```

---

### POST /conversations/{id}/close
Close conversation.

**Request**:
```json
{
  "close_reason": "resolved",
  "notes": "Customer issue resolved"
}
```

**Response** (200):
```json
{
  "id": "uuid",
  "status": "closed",
  "closed_at": "2026-01-05T12:00:00Z",
  "closed_by": {"id": "uuid", "full_name": "Maria Garcia"},
  "close_reason": "resolved"
}
```

---

## 4. Messages

### GET /conversations/{id}/messages
Get messages for conversation.

**Query Params**:
- `before`: Timestamp (pagination)
- `limit`: Max 100

**Response** (200):
```json
{
  "messages": [
    {
      "id": "uuid",
      "direction": "inbound",
      "sender_type": "customer",
      "sender": {
        "id": "customer_uuid",
        "name": "Juan Lopez"
      },
      "content_type": "text",
      "content_text": "Hola, necesito ayuda",
      "status": "delivered",
      "sent_at": "2026-01-05T11:30:00Z",
      "delivered_at": "2026-01-05T11:30:05Z",
      "read_at": "2026-01-05T11:30:10Z"
    },
    {
      "id": "uuid",
      "direction": "outbound",
      "sender_type": "agent",
      "sender": {
        "id": "agent_uuid",
        "name": "Maria Garcia"
      },
      "content_type": "text",
      "content_text": "Hola Juan, ¿en qué puedo ayudarte?",
      "status": "read",
      "sent_at": "2026-01-05T11:32:00Z"
    }
  ],
  "has_more": false
}
```

---

### POST /conversations/{id}/messages
Send message to customer.

**Request**:
```json
{
  "content_type": "text",
  "content_text": "Hola, ¿cómo puedo ayudarte?"
}
```

**Response** (201):
```json
{
  "id": "uuid",
  "direction": "outbound",
  "sender_type": "agent",
  "content_type": "text",
  "content_text": "Hola, ¿cómo puedo ayudarte?",
  "status": "pending",
  "sent_at": "2026-01-05T12:00:00Z"
}
```

**Errors**:
- 400: Outside 24h window (WhatsApp)
- 403: Not assigned to conversation

---

### POST /conversations/{id}/messages/template
Send WhatsApp template message.

**Request**:
```json
{
  "template_name": "follow_up",
  "params": ["Juan", "tu consulta"]
}
```

**Response** (201):
```json
{
  "id": "uuid",
  "content_type": "template",
  "status": "pending"
}
```

---

## 5. Tags & Notes

### GET /tags
List tags.

**Query Params**:
- `team_id`: Filter by team (null = global)

**Response** (200):
```json
{
  "tags": [
    {"id": "uuid", "name": "VIP", "color": "#FF0000", "team_id": null},
    {"id": "uuid", "name": "Urgent", "color": "#FFA500", "team_id": "sales_uuid"}
  ]
}
```

---

### POST /conversations/{id}/tags
Add tag to conversation.

**Request**:
```json
{
  "tag_id": "uuid"
}
```

**Response** (200):
```json
{
  "conversation_id": "uuid",
  "tags": [
    {"id": "uuid", "name": "VIP", "color": "#FF0000"}
  ]
}
```

---

### POST /conversations/{id}/notes
Add note to conversation.

**Request**:
```json
{
  "content": "Customer mentioned they're interested in enterprise plan",
  "is_pinned": false
}
```

**Response** (201):
```json
{
  "id": "uuid",
  "content": "Customer mentioned they're interested in enterprise plan",
  "author": {"id": "uuid", "full_name": "Maria Garcia"},
  "is_pinned": false,
  "created_at": "2026-01-05T12:00:00Z"
}
```

---

## 6. Internal Chat

### POST /internal/threads
Create internal chat thread.

**Request**:
```json
{
  "title": "Sales Team Sync",
  "member_ids": ["agent1_uuid", "agent2_uuid"]
}
```

**Response** (201):
```json
{
  "id": "uuid",
  "title": "Sales Team Sync",
  "created_by": {"id": "uuid", "full_name": "Maria Garcia"},
  "members": [
    {"id": "agent1_uuid", "full_name": "Juan Perez"},
    {"id": "agent2_uuid", "full_name": "Ana Lopez"}
  ],
  "created_at": "2026-01-05T12:00:00Z"
}
```

---

### GET /internal/threads
List threads for current user.

**Response** (200):
```json
{
  "threads": [
    {
      "id": "uuid",
      "title": "Sales Team Sync",
      "unread_count": 3,
      "last_message": {
        "content": "Let's discuss the new campaign",
        "sender": {"id": "uuid", "full_name": "Juan Perez"},
        "sent_at": "2026-01-05T11:45:00Z"
      },
      "members": [...]
    }
  ]
}
```

---

### POST /internal/threads/{id}/messages
Send message in thread.

**Request**:
```json
{
  "content": "Sounds good, let's meet at 3pm"
}
```

**Response** (201):
```json
{
  "id": "uuid",
  "content": "Sounds good, let's meet at 3pm",
  "sender": {"id": "uuid", "full_name": "Maria Garcia"},
  "created_at": "2026-01-05T12:00:00Z"
}
```

---

## 7. Reports & Metrics

### GET /reports/team/{team_id}
Team performance metrics.

**Query Params**:
- `start_date`: YYYY-MM-DD
- `end_date`: YYYY-MM-DD

**Response** (200):
```json
{
  "team": {"id": "uuid", "name": "Sales"},
  "period": {
    "start": "2026-01-01",
    "end": "2026-01-05"
  },
  "metrics": {
    "conversations_created": 120,
    "conversations_closed": 110,
    "avg_frt_seconds": 180,
    "avg_resolution_seconds": 1800,
    "p50_frt_seconds": 120,
    "p95_frt_seconds": 300,
    "current_backlog": 12
  },
  "agents": [
    {
      "id": "uuid",
      "full_name": "Maria Garcia",
      "conversations_handled": 25,
      "avg_frt_seconds": 150
    }
  ]
}
```

---

### GET /reports/agent/{agent_id}
Agent performance metrics.

**Response** (200):
```json
{
  "agent": {"id": "uuid", "full_name": "Maria Garcia"},
  "period": {"start": "2026-01-01", "end": "2026-01-05"},
  "metrics": {
    "conversations_handled": 25,
    "messages_sent": 150,
    "avg_frt_seconds": 150,
    "avg_resolution_seconds": 1500
  }
}
```

---

## 8. WebSocket Events

### Connection
```
wss://api.max.internal/v1/ws?token=<jwt_token>
```

### Events (Server → Client)

#### conversation.new
```json
{
  "event": "conversation.new",
  "data": {
    "conversation_id": "uuid",
    "team_id": "sales_uuid",
    "customer": {"name": "Juan Lopez"},
    "preview": "Hola, necesito ayuda"
  }
}
```

#### message.received
```json
{
  "event": "message.received",
  "data": {
    "conversation_id": "uuid",
    "message": {
      "id": "uuid",
      "content_text": "Gracias",
      "sent_at": "2026-01-05T12:00:00Z"
    }
  }
}
```

#### conversation.assigned
```json
{
  "event": "conversation.assigned",
  "data": {
    "conversation_id": "uuid",
    "assigned_to": {"id": "uuid", "full_name": "Maria Garcia"}
  }
}
```

#### agent.typing
```json
{
  "event": "agent.typing",
  "data": {
    "conversation_id": "uuid",
    "agent": {"id": "uuid", "full_name": "Maria Garcia"},
    "is_typing": true
  }
}
```

### Events (Client → Server)

#### typing.start
```json
{
  "event": "typing.start",
  "conversation_id": "uuid"
}
```

#### typing.stop
```json
{
  "event": "typing.stop",
  "conversation_id": "uuid"
}
```

---

**Next**: See [Integration Hub](./06-integration-hub.md) for external system integrations.
