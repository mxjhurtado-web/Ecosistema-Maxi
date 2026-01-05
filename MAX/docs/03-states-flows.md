# D. States & Flows

## Conversation States

### State Machine

```
┌─────┐
│ NEW │ (Customer sends first message)
└──┬──┘
   │
   ▼
┌────────┐
│ TRIAGE │ (AI/system routing flow)
└───┬────┘
    │
    ├─────────────────┐
    │                 │
    ▼                 ▼
┌────────┐      ┌──────────┐
│ QUEUED │      │ ASSIGNED │ (Manual assignment skips queue)
└───┬────┘      └────┬─────┘
    │                │
    │                │
    └────────┬───────┘
             │
             ▼
      ┌──────────────┐
      │   ASSIGNED   │ (Agent actively working)
      └──────┬───────┘
             │
             ├──────────────┬──────────────┐
             │              │              │
             ▼              ▼              ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌────────┐
    │ PENDING_CUSTOMER│ │ PENDING_AGENT   │ │ CLOSED │
    └────────┬────────┘ └────────┬────────┘ └────────┘
             │                   │
             └─────────┬─────────┘
                       │
                       ▼
                ┌──────────────┐
                │   ASSIGNED   │ (Back to active)
                └──────────────┘
```

### State Definitions

| State | Description | Triggers | SLA Impact |
|-------|-------------|----------|------------|
| `new` | First message received, not yet processed | Inbound message from new customer | FRT starts |
| `triage` | Routing flow in progress | Worker picks up new conversation | - |
| `queued` | Waiting in team queue for assignment | Triage complete, no agent assigned | Queue time tracked |
| `assigned` | Agent actively working on conversation | Manual/auto assignment | FRT stops on first reply |
| `pending_customer` | Waiting for customer response | Agent sent message, no reply yet | Paused |
| `pending_agent` | Waiting for agent response (customer replied) | Customer sent new message | SLA resumes |
| `closed` | Conversation resolved | Agent closes with reason | Resolution time recorded |

### State Transitions

```python
ALLOWED_TRANSITIONS = {
    'new': ['triage'],
    'triage': ['queued', 'assigned'],  # assigned if manual override
    'queued': ['assigned', 'closed'],  # closed if spam/duplicate
    'assigned': ['pending_customer', 'pending_agent', 'closed'],
    'pending_customer': ['pending_agent', 'closed'],
    'pending_agent': ['assigned', 'closed'],
    'closed': ['assigned']  # reopen
}
```

**Validation**: API rejects invalid transitions (e.g., `new` → `closed`).

---

## Triage Flow

### Objectives
1. Identify customer intent (Sales / Support / Customer Service)
2. Collect minimal context for routing
3. Route to correct team queue
4. Handle "I want a human" escape hatch

### Flow Steps

#### Step 0: Welcome Message
```
Trigger: First message from customer
Action: Send welcome + menu
```

**Message Template**:
```
¡Hola! 👋 Bienvenido a MAX.

¿En qué podemos ayudarte hoy?

1️⃣ Ventas - Comprar productos o servicios
2️⃣ Soporte - Problemas técnicos o ayuda
3️⃣ Servicio al Cliente - Consultar transacciones

Responde con el número o escribe tu consulta.
```

**AI Behavior**:
- Parse response (1/2/3 or natural language)
- Detect keywords: "comprar", "problema", "transacción", etc.
- Fallback: If unclear, ask again (max 1 retry)

---

#### Step 1: Team Selection

**Sales Path**:
```
Q: "¿Qué producto te interesa?"
A: Customer responds
→ Route to Sales queue with metadata: {product_interest: "..."}
```

**Support Path**:
```
Q: "¿Qué tipo de problema tienes? (técnico, acceso, otro)"
A: Customer responds
→ Route to Support queue with metadata: {issue_type: "..."}
```

**Customer Service Path**:
```
Q: "¿Tienes un número de transacción?"
A: Customer responds
→ Route to Customer Service queue with metadata: {transaction_id: "..." or null}
```

---

#### Step 2: Route to Queue

**Routing Decision**:
```json
{
  "conversation_id": "uuid",
  "team": "sales",
  "priority": "normal",
  "metadata": {
    "triage_responses": ["1", "Quiero comprar un plan"],
    "product_interest": "plan premium",
    "language": "es"
  },
  "routed_at": "2026-01-05T12:00:00Z"
}
```

**Action**:
1. Update `conversations.team_id = sales_team_id`
2. Update `conversations.status = 'queued'`
3. Create event: `triage.completed`
4. Notify team supervisors via WebSocket

---

### Escape Hatch: "Quiero Hablar con un Humano"

**Trigger**: Customer says "humano", "agente", "persona", etc.

**Action**:
1. Skip remaining triage questions
2. Route to general triage queue (no team)
3. Flag as `priority: high`
4. Notify all supervisors

**Message**:
```
Entendido, te conectaré con un agente humano enseguida.
```

---

### Fallback: Unclear Intent

**After 2 failed attempts**:
```
No problem, te conectaré con un agente que podrá ayudarte mejor.
→ Route to triage queue (supervisor assigns manually)
```

---

## Assignment Logic

### Phase 1: Manual Assignment

#### Option A: Supervisor Assigns
```
UI: Supervisor sees queue → clicks conversation → assigns to agent
API: POST /conversations/{id}/assign
Body: {"assigned_to": "agent_uuid"}
```

**Validation**:
- Agent must be in same team
- Agent must be active (`is_active = true`)
- Conversation must be in `queued` or `triage` state

**Actions**:
1. Update `conversations.assigned_to = agent_uuid`
2. Update `conversations.status = 'assigned'`
3. Update `conversations.assigned_at = NOW()`
4. Create event: `conversation.assigned`
5. Push WebSocket event to agent

---

#### Option B: Agent Takes from Queue
```
UI: Agent sees team queue → clicks "Take"
API: POST /conversations/{id}/take
```

**Validation**:
- Agent must be in conversation's team
- Conversation must be `queued`
- Agent cannot have > 5 active conversations (configurable limit)

**Actions**: Same as Option A

---

### Phase 2: Auto-Assignment (Future)

**Capacity-Based Algorithm**:
```python
def auto_assign(conversation):
    team = conversation.team
    agents = get_active_agents(team)
    
    # Calculate capacity
    agent_loads = []
    for agent in agents:
        active_convos = count_active_conversations(agent)
        max_capacity = agent.max_concurrent_conversations  # e.g., 5
        load_pct = active_convos / max_capacity
        agent_loads.append((agent, load_pct))
    
    # Sort by lowest load
    agent_loads.sort(key=lambda x: x[1])
    
    # Assign to least loaded agent
    selected_agent = agent_loads[0][0]
    assign_conversation(conversation, selected_agent)
```

**Triggers**:
- New conversation enters `queued` state
- Agent closes conversation (free up capacity)

**Fallback**: If all agents at capacity, stay in queue

---

## Transfer Logic

**Scenario**: Agent realizes conversation belongs to different team.

```
API: POST /conversations/{id}/transfer
Body: {
  "to_team_id": "support_uuid",
  "to_agent_id": null,  # or specific agent
  "reason": "Customer needs technical support"
}
```

**Actions**:
1. Update `conversations.team_id = support_uuid`
2. Update `conversations.assigned_to = null` (unless `to_agent_id` specified)
3. Update `conversations.status = 'queued'` (or `assigned` if specific agent)
4. Create event: `conversation.transferred`
5. Add system message: "Conversation transferred to Support team"
6. Notify new team supervisors

---

## Close Logic

**Trigger**: Agent clicks "Close Conversation"

```
API: POST /conversations/{id}/close
Body: {
  "close_reason": "resolved|spam|duplicate|customer_unresponsive",
  "notes": "Optional closing notes"
}
```

**Validation**:
- Only assigned agent, team lead, or supervisor can close
- Must provide `close_reason`

**Actions**:
1. Update `conversations.status = 'closed'`
2. Update `conversations.closed_at = NOW()`
3. Update `conversations.closed_by = current_user_id`
4. Update `conversations.close_reason = reason`
5. Create event: `conversation.closed`
6. Calculate resolution time: `closed_at - first_message_at`
7. Update agent stats

**Close Reasons**:
- `resolved`: Issue fixed, customer satisfied
- `spam`: Spam or irrelevant message
- `duplicate`: Duplicate of another conversation
- `customer_unresponsive`: No reply after 48 hours

---

## Reopen Logic

**Trigger**: Customer sends message to closed conversation (within 7 days)

**Auto-Reopen**:
1. Update `conversations.status = 'assigned'` (if previous agent available)
2. Or `status = 'queued'` (if agent offline/unavailable)
3. Create event: `conversation.reopened`
4. Notify previous agent or team

**After 7 Days**: Create new conversation instead

---

## WhatsApp-Specific Rules

### 24-Hour Window

**Rule**: Can only send freeform messages within 24h of last customer message.

**Implementation**:
```python
def can_send_freeform(conversation):
    last_customer_msg = get_last_customer_message(conversation)
    if not last_customer_msg:
        return False
    
    elapsed = now() - last_customer_msg.sent_at
    return elapsed < timedelta(hours=24)
```

**Outside 24h**: Must use approved message templates.

**UI Indicator**: Show "24h window expires in 3 hours" warning.

---

### Message Templates

**Use Cases**:
- Follow-up after 24h window closed
- Proactive outreach (e.g., "Your order shipped")

**Example Template**:
```json
{
  "name": "follow_up",
  "language": "es",
  "components": [
    {
      "type": "body",
      "text": "Hola {{1}}, ¿aún necesitas ayuda con {{2}}?"
    }
  ]
}
```

**API Call**:
```python
send_template_message(
    phone=customer.external_id,
    template="follow_up",
    params=["Juan", "tu consulta"]
)
```

---

### Delivery Status Tracking

**Webhook Events**:
- `sent`: Message sent to WhatsApp
- `delivered`: Delivered to customer's device
- `read`: Customer opened message
- `failed`: Delivery failed

**Actions**:
1. Update `messages.status`
2. Update `messages.delivered_at` or `read_at`
3. Push WebSocket event to agent UI
4. If `failed`: Log error, retry (max 3 attempts)

---

## Example Flow: End-to-End

### Scenario: Customer Needs Support

```
1. Customer (WhatsApp): "Hola, no puedo acceder a mi cuenta"
   → Conversation created (status: new)
   → Triage worker triggered

2. AI: "¡Hola! 👋 ¿En qué podemos ayudarte? 1️⃣ Ventas 2️⃣ Soporte 3️⃣ Servicio"
   → Conversation status: triage

3. Customer: "2"
   → AI detects: Support team

4. AI: "¿Qué tipo de problema? (técnico, acceso, otro)"
   → Waiting for response

5. Customer: "acceso"
   → Routing decision: team=Support, metadata={issue_type: "acceso"}
   → Conversation status: queued
   → Notify Support supervisors

6. Agent (Maria) clicks "Take"
   → Conversation assigned to Maria
   → Conversation status: assigned
   → WebSocket pushes conversation to Maria's inbox

7. Maria: "Hola, soy Maria. ¿Qué mensaje de error ves?"
   → Message sent (status: sent)
   → FRT recorded: 2 minutes

8. Customer: "Dice 'contraseña incorrecta'"
   → Conversation status: pending_agent

9. Maria: "Te envío un link para resetear tu contraseña: [link]"
   → Message sent

10. Customer: "Listo, ya pude entrar. Gracias!"
    → Conversation status: pending_agent

11. Maria clicks "Close" (reason: resolved)
    → Conversation status: closed
    → Resolution time: 8 minutes
    → Agent stats updated
```

---

**Next**: See [RBAC & Permissions](./04-rbac.md) for role-based access control.
