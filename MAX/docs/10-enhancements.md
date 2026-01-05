# Enhancements & Advanced Features

This document covers critical and important enhancements added to the MAX platform architecture.

---

## 1. Media Handling (WhatsApp & Chat App)

### Overview
Handle images, videos, audio, and documents from customers.

### Flow

#### Inbound Media (WhatsApp)
```
1. Webhook receives message with media_id
2. Worker downloads media from WhatsApp API
3. Upload to S3/CloudFlare R2
4. Generate signed URL (expires 7 days)
5. Store in media_files table
6. Display in agent UI
```

#### Implementation
```python
async def handle_whatsapp_media(message_data):
    media_id = message_data['media_id']
    media_type = message_data['type']  # image, video, audio, document
    
    # Download from WhatsApp
    media_url = await whatsapp_api.get_media_url(media_id)
    media_content = await download_file(media_url)
    
    # Upload to S3
    storage_key = f"media/{conversation_id}/{message_id}/{filename}"
    storage_url = await s3.upload(
        key=storage_key,
        content=media_content,
        content_type=mime_type
    )
    
    # Generate signed URL (7 days)
    signed_url = await s3.generate_signed_url(storage_key, expires_in=604800)
    
    # Save to database
    await MediaFile.create(
        message_id=message_id,
        channel_media_id=media_id,
        media_type=media_type,
        storage_url=signed_url,
        storage_key=storage_key,
        file_size_bytes=len(media_content)
    )
```

### Cleanup Job
```python
# Daily job: delete expired media
async def cleanup_expired_media():
    expired = await MediaFile.filter(
        expires_at__lt=now()
    )
    
    for media in expired:
        await s3.delete(media.storage_key)
        await media.delete()
```

---

## 2. Customer Identity Resolution

### Problem
Customer contacts via WhatsApp (+1234567890) and Chat App (customer_abc123). System treats as 2 different customers.

### Solution
Link multiple identities to single customer profile.

### UI Flow
```
Agent views conversation from WhatsApp customer
→ Sees "Link Identity" button
→ Searches for Chat App customer by email/ID
→ Confirms link
→ All conversations from both channels appear in unified profile
```

### Implementation
```python
async def link_customer_identities(
    primary_customer_id: UUID,
    secondary_customer_id: UUID,
    linked_by: UUID
):
    # Get secondary customer's identities
    secondary_identities = await CustomerIdentity.filter(
        customer_id=secondary_customer_id
    )
    
    # Move identities to primary customer
    for identity in secondary_identities:
        identity.customer_id = primary_customer_id
        identity.linked_by = linked_by
        await identity.save()
    
    # Move conversations
    await Conversation.filter(
        customer_id=secondary_customer_id
    ).update(customer_id=primary_customer_id)
    
    # Soft delete secondary customer
    await Customer.filter(id=secondary_customer_id).update(is_active=False)
```

---

## 3. Canned Responses

### Overview
Pre-defined quick replies for common scenarios.

### UI Flow
```
Agent typing in message box
→ Types "/greeting"
→ Autocomplete shows: "¡Hola! Gracias por contactarnos..."
→ Agent presses Tab/Enter
→ Message inserted
```

### API

#### GET /canned-responses
```json
{
  "responses": [
    {
      "id": "uuid",
      "shortcut": "/greeting",
      "title": "Saludo inicial",
      "content": "¡Hola! Gracias por contactarnos. ¿En qué puedo ayudarte?",
      "category": "general",
      "usage_count": 245
    }
  ]
}
```

#### POST /canned-responses
```json
{
  "team_id": "sales_uuid",
  "shortcut": "/pricing",
  "title": "Información de precios",
  "content": "Nuestros planes empiezan desde $99/mes...",
  "category": "sales"
}
```

### Variables Support
```
Content: "Hola {{customer_name}}, tu pedido {{order_id}} está listo."

Agent uses /order_ready
→ System replaces:
  {{customer_name}} → "Juan"
  {{order_id}} → "ORD-123"
→ Final: "Hola Juan, tu pedido ORD-123 está listo."
```

---

## 4. SLA Management

### Overview
Define and track Service Level Agreements per team and priority.

### Configuration
```sql
-- Sales team SLAs
INSERT INTO sla_policies (team_id, priority, frt_target_seconds, resolution_target_seconds) VALUES
    ('sales_uuid', 'urgent', 180, 900),    -- 3min FRT, 15min resolution
    ('sales_uuid', 'normal', 600, 3600);   -- 10min FRT, 1h resolution
```

### Worker: SLA Monitor
```python
@celery.task
async def monitor_sla_violations():
    """Run every minute"""
    
    # Check FRT violations
    conversations = await Conversation.filter(
        status__in=['queued', 'assigned'],
        first_response_at__isnull=True
    ).prefetch_related('team', 'sla_policy')
    
    for conv in conversations:
        sla = await get_sla_policy(conv.team_id, conv.priority)
        elapsed = (now() - conv.first_message_at).total_seconds()
        
        if elapsed > sla.frt_target_seconds:
            # Create violation
            await SLAViolation.create(
                conversation_id=conv.id,
                sla_policy_id=sla.id,
                violation_type='frt',
                target_seconds=sla.frt_target_seconds,
                actual_seconds=int(elapsed)
            )
            
            # Escalate if configured
            if sla.escalation_after_seconds and elapsed > sla.escalation_after_seconds:
                await escalate_conversation(conv)
```

### Dashboard
```
Team: Sales
SLA Compliance (Last 7 days):
  FRT: 92% (target: 95%)
  Resolution: 88% (target: 90%)

Violations:
  - Conv #123: FRT 12min (target: 5min) - ESCALATED
  - Conv #456: Resolution 2h (target: 1h)
```

---

## 5. Business Hours

### Overview
Define team operating hours and handle after-hours messages.

### Configuration
```sql
-- Support team: Mon-Fri 9am-6pm
INSERT INTO business_hours (team_id, day_of_week, open_time, close_time) VALUES
    ('support_uuid', 0, '09:00', '18:00'),  -- Monday
    ('support_uuid', 1, '09:00', '18:00'),  -- Tuesday
    ...
```

### Implementation
```python
def is_within_business_hours(team_id: UUID) -> bool:
    now_local = now().astimezone(timezone('America/Mexico_City'))
    day_of_week = now_local.weekday()
    current_time = now_local.time()
    
    hours = await BusinessHours.get_or_none(
        team_id=team_id,
        day_of_week=day_of_week,
        is_active=True
    )
    
    if not hours:
        return False  # No hours defined = closed
    
    return hours.open_time <= current_time <= hours.close_time
```

### After-Hours Handling
```python
async def handle_new_conversation(conversation):
    if not is_within_business_hours(conversation.team_id):
        # Send auto-response
        await send_message(
            conversation_id=conversation.id,
            content_text=(
                "Gracias por contactarnos. Nuestro horario es "
                "Lunes a Viernes de 9am a 6pm. "
                "Te responderemos en cuanto abramos."
            ),
            sender_type='system'
        )
        
        # Lower priority
        conversation.priority = 'low'
        await conversation.save()
```

---

## 6. WhatsApp Templates Management

### Overview
CRUD for WhatsApp message templates (required for messages outside 24h window).

### API

#### POST /whatsapp-templates
```json
{
  "name": "order_shipped",
  "language": "es",
  "category": "UTILITY",
  "components": [
    {
      "type": "BODY",
      "text": "Hola {{1}}, tu pedido {{2}} ha sido enviado. Tracking: {{3}}"
    }
  ]
}
```

**Response**:
```json
{
  "id": "uuid",
  "name": "order_shipped",
  "status": "PENDING",
  "message": "Template submitted to WhatsApp for approval"
}
```

#### GET /whatsapp-templates
```json
{
  "templates": [
    {
      "id": "uuid",
      "name": "order_shipped",
      "language": "es",
      "status": "APPROVED",
      "whatsapp_template_id": "1234567890"
    }
  ]
}
```

### Webhook: Template Status Update
```python
@app.post("/webhooks/whatsapp/template-status")
async def handle_template_status(data: dict):
    """WhatsApp notifies when template approved/rejected"""
    
    template = await WhatsAppTemplate.get(name=data['name'])
    template.status = data['status']
    template.whatsapp_template_id = data.get('id')
    template.rejection_reason = data.get('rejection_reason')
    await template.save()
    
    # Notify creator
    await notify_user(
        template.created_by,
        f"Template '{template.name}' {data['status'].lower()}"
    )
```

---

## 7. Rate Limiting (Customer-Side)

### Overview
Prevent spam by limiting messages per customer.

### Limits
- **Messages**: 20 per minute
- **Conversations**: 5 per hour

### Implementation
```python
async def check_customer_rate_limit(customer_id: UUID) -> bool:
    """Check if customer exceeded rate limit"""
    
    window_start = now() - timedelta(minutes=1)
    
    # Get or create bucket
    bucket, created = await RateLimitBucket.get_or_create(
        customer_id=customer_id,
        bucket_type='message',
        window_start=window_start,
        defaults={'window_end': now()}
    )
    
    if bucket.count >= 20:
        bucket.is_blocked = True
        await bucket.save()
        
        # Notify supervisor
        await notify_supervisor(
            f"Customer {customer_id} blocked for spam (20+ msgs/min)"
        )
        
        return False
    
    bucket.count += 1
    await bucket.save()
    return True
```

### Cleanup
```python
# Delete old buckets (daily)
await RateLimitBucket.filter(
    window_end__lt=now() - timedelta(days=1)
).delete()
```

---

## 8. Skills-Based Routing (Future)

### Overview
Route conversations to agents with specific skills.

### Configuration
```sql
-- Agent skills
INSERT INTO agent_skills (user_id, skill_name, proficiency_level) VALUES
    ('agent1_uuid', 'english', 5),
    ('agent1_uuid', 'billing', 4),
    ('agent2_uuid', 'spanish', 5),
    ('agent2_uuid', 'technical_support', 5);
```

### Auto-Assignment Logic
```python
async def auto_assign_with_skills(conversation):
    # Get required skills from triage
    required_skills = conversation.metadata.get('required_skills', [])
    
    if not required_skills:
        # Fallback to capacity-based
        return await auto_assign_capacity_based(conversation)
    
    # Find agents with required skills
    agents = await User.filter(
        team_memberships__team_id=conversation.team_id,
        agent_skills__skill_name__in=required_skills,
        is_active=True
    ).distinct()
    
    # Sort by proficiency and current load
    best_agent = await select_best_agent(agents, required_skills)
    
    await assign_conversation(conversation, best_agent)
```

---

## 9. Outbound Webhooks

### Overview
Notify external systems of MAX events.

### Configuration
```sql
INSERT INTO webhook_subscriptions (url, events, secret) VALUES
    ('https://crm.example.com/webhooks/max',
     ARRAY['conversation.closed', 'conversation.assigned'],
     'secret_key_123');
```

### Delivery
```python
async def send_webhook(subscription: WebhookSubscription, event_type: str, payload: dict):
    """Send webhook with retry logic"""
    
    # Generate signature
    signature = hmac.new(
        subscription.secret.encode(),
        json.dumps(payload).encode(),
        hashlib.sha256
    ).hexdigest()
    
    headers = {
        'X-MAX-Signature': signature,
        'X-MAX-Event': event_type
    }
    
    for attempt in range(1, subscription.retry_count + 1):
        try:
            response = await httpx.post(
                subscription.url,
                json=payload,
                headers=headers,
                timeout=subscription.timeout_seconds
            )
            
            # Log delivery
            await WebhookDelivery.create(
                subscription_id=subscription.id,
                event_type=event_type,
                payload=payload,
                status_code=response.status_code,
                response_body=response.text[:1000],
                attempt_number=attempt
            )
            
            if response.status_code < 500:
                break  # Success or client error (don't retry)
                
        except Exception as e:
            await WebhookDelivery.create(
                subscription_id=subscription.id,
                event_type=event_type,
                payload=payload,
                error=str(e),
                attempt_number=attempt
            )
            
            if attempt < subscription.retry_count:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

---

## 10. Customer Context Panel

### Overview
Sidebar showing complete customer history.

### UI Components
```
┌─────────────────────────────────┐
│ Customer: Juan Lopez            │
│ +1234567890 (WhatsApp)          │
│ customer_abc123 (Chat App)      │
├─────────────────────────────────┤
│ Previous Conversations (3)      │
│ • [Closed] Product inquiry      │
│ • [Closed] Billing question     │
│ • [Closed] Technical support    │
├─────────────────────────────────┤
│ Recent Transactions (2)         │
│ • $500 - Completed (Jan 3)      │
│ • $250 - Completed (Dec 28)     │
├─────────────────────────────────┤
│ Open Tickets (1)                │
│ • TICKET-456: Login issue       │
├─────────────────────────────────┤
│ Tags                            │
│ • VIP Customer                  │
│ • Prefers English               │
└─────────────────────────────────┘
```

### API
```
GET /customers/{id}/context
```

**Response**:
```json
{
  "customer": {
    "id": "uuid",
    "name": "Juan Lopez",
    "identities": [
      {"channel": "whatsapp", "external_id": "+1234567890"},
      {"channel": "chat_app", "external_id": "customer_abc123"}
    ]
  },
  "previous_conversations": [
    {
      "id": "uuid",
      "status": "closed",
      "close_reason": "resolved",
      "created_at": "2026-01-03T10:00:00Z"
    }
  ],
  "recent_transactions": [
    {
      "transaction_id": "TXN-123",
      "amount": 500.00,
      "status": "completed",
      "created_at": "2026-01-03T12:00:00Z"
    }
  ],
  "open_tickets": [
    {
      "ticket_id": "TICKET-456",
      "subject": "Login issue",
      "status": "open"
    }
  ],
  "tags": ["VIP", "Prefers English"]
}
```

---

## Implementation Priority

### MVP 1 (Critical)
- ✅ Media handling
- ✅ Canned responses
- ✅ Rate limiting (customer-side)

### MVP 2 (Important)
- ✅ SLA management
- ✅ Customer identity resolution
- ✅ Business hours
- ✅ WhatsApp templates CRUD

### MVP 3 (Nice to Have)
- Skills-based routing
- Outbound webhooks
- Customer context panel

---

**Next**: See implementation details in respective documents.
