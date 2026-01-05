# H. AI Tool Gateway

## Overview

The **AI Tool Gateway** is a security layer between AI agents and external integrations. It ensures:
- AI never accesses API keys/secrets directly
- All tool calls are validated and audited
- Sensitive operations require human confirmation
- PII is redacted from logs
- Rate limits prevent abuse

---

## Architecture

```
┌─────────────┐
│  AI Agent   │
└──────┬──────┘
       │ Tool request
       ▼
┌──────────────────────────────────────┐
│      AI Tool Gateway                 │
├──────────────────────────────────────┤
│  1. Permission Validation            │
│  2. Input Sanitization               │
│  3. Rate Limiting                    │
│  4. Confirmation Token Validation    │
│  5. Execute Tool                     │
│  6. PII Redaction                    │
│  7. Audit Logging                    │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────┐
│ Integration Hub  │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  External API    │
└──────────────────┘
```

---

## Tool Definitions

### 1. search_tickets

**Purpose**: Search support tickets for customer.

**Input Schema**:
```json
{
  "customer_id": "uuid",
  "status": "open|closed|all",
  "limit": 10
}
```

**Permissions**:
- All roles
- Must have access to conversation

**Rate Limit**: 20 calls/hour per conversation

**Implementation**:
```python
@tool
async def search_tickets(
    customer_id: str,
    status: str = "all",
    limit: int = 10
) -> List[Dict]:
    """Search tickets for customer"""
    
    # Validate inputs
    if limit > 50:
        raise ValueError("Limit cannot exceed 50")
    
    # Call integration
    adapter = get_adapter("ticketing")
    tickets = await adapter.search_tickets(
        customer_id=customer_id,
        status=status,
        limit=limit
    )
    
    return tickets
```

**Example Output**:
```json
[
  {
    "ticket_id": "TICKET-123",
    "subject": "Login issue",
    "status": "open",
    "created_at": "2026-01-05T10:00:00Z"
  }
]
```

---

### 2. get_transaction_status

**Purpose**: Get status of specific transaction.

**Input Schema**:
```json
{
  "transaction_id": "string"
}
```

**Permissions**:
- All roles
- Must have access to conversation

**Rate Limit**: 30 calls/hour per conversation

**Implementation**:
```python
@tool
async def get_transaction_status(transaction_id: str) -> Dict:
    """Get transaction status"""
    
    # Validate format
    if not transaction_id.startswith("TXN-"):
        raise ValueError("Invalid transaction ID format")
    
    # Call integration
    adapter = get_adapter("transaction_status")
    status = await adapter.get_transaction_status(transaction_id)
    
    return status
```

**Example Output**:
```json
{
  "transaction_id": "TXN-12345",
  "status": "completed",
  "amount": 500.00,
  "currency": "USD",
  "created_at": "2026-01-05T10:00:00Z"
}
```

---

### 3. create_transaction_draft

**Purpose**: Create draft transaction (not committed).

**Input Schema**:
```json
{
  "customer_id": "uuid",
  "amount": 500.00,
  "description": "Product purchase",
  "metadata": {}
}
```

**Permissions**:
- Sales team only
- Must have access to conversation

**Rate Limit**: 10 calls/hour per conversation

**Validation Rules**:
- `amount` must be > 0 and < 10000
- `description` required, max 500 chars
- `metadata` allowlisted fields only

**Implementation**:
```python
@tool
@require_team("sales")
async def create_transaction_draft(
    customer_id: str,
    amount: float,
    description: str,
    metadata: Dict = None
) -> Dict:
    """Create draft transaction"""
    
    # Validate amount
    if amount <= 0 or amount > 10000:
        raise ValueError("Amount must be between 0 and 10000")
    
    # Validate description
    if not description or len(description) > 500:
        raise ValueError("Description required, max 500 chars")
    
    # Sanitize metadata (allowlist)
    allowed_fields = ['product_id', 'quantity', 'notes']
    clean_metadata = {
        k: v for k, v in (metadata or {}).items()
        if k in allowed_fields
    }
    
    # Call integration
    adapter = get_adapter("transaction_create")
    draft = await adapter.create_draft_transaction(
        customer_id=customer_id,
        amount=amount,
        description=description,
        metadata=clean_metadata
    )
    
    # Store draft_id in conversation metadata for confirmation
    await store_pending_draft(conversation_id, draft["draft_id"])
    
    return draft
```

**Example Output**:
```json
{
  "draft_id": "DRAFT-abc123",
  "status": "pending_confirmation",
  "amount": 500.00,
  "expires_at": "2026-01-05T12:30:00Z"
}
```

---

### 4. commit_transaction

**Purpose**: Finalize draft transaction (requires confirmation).

**Input Schema**:
```json
{
  "draft_id": "DRAFT-abc123",
  "confirmation_token": "token_from_customer"
}
```

**Permissions**:
- Sales team only
- Must have access to conversation
- Requires valid confirmation token

**Rate Limit**: 5 calls/hour per conversation

**Two-Phase Commit**:

#### Phase 1: AI creates draft
```
AI: "I can create a transaction for $500. Do you want to proceed?"
Customer: "Yes"
AI: create_transaction_draft(amount=500, ...)
→ Returns draft_id
```

#### Phase 2: Customer confirms
```
AI: "Please confirm by typing 'CONFIRM-abc123'"
Customer: "CONFIRM-abc123"
AI: Extracts confirmation token
AI: commit_transaction(draft_id, confirmation_token)
→ Transaction finalized
```

**Implementation**:
```python
@tool
@require_team("sales")
async def commit_transaction(
    draft_id: str,
    confirmation_token: str
) -> Dict:
    """Commit draft transaction"""
    
    # Validate confirmation token
    expected_token = f"CONFIRM-{draft_id.split('-')[1]}"
    if confirmation_token != expected_token:
        raise ValueError("Invalid confirmation token")
    
    # Check draft exists and belongs to this conversation
    draft = await get_pending_draft(conversation_id, draft_id)
    if not draft:
        raise ValueError("Draft not found or expired")
    
    # Additional validation for high amounts
    if draft["amount"] > 1000:
        # Require supervisor approval
        if not await has_supervisor_approval(conversation_id, draft_id):
            raise ValueError("Supervisor approval required for amounts > $1000")
    
    # Generate idempotency key
    idempotency_key = f"{conversation_id}:{draft_id}"
    
    # Call integration
    adapter = get_adapter("transaction_create")
    transaction = await adapter.commit_transaction(
        draft_id=draft_id,
        idempotency_key=idempotency_key
    )
    
    # Clear pending draft
    await clear_pending_draft(conversation_id, draft_id)
    
    return transaction
```

**Example Output**:
```json
{
  "transaction_id": "TXN-12345",
  "status": "completed",
  "amount": 500.00
}
```

---

## Confirmation Token Flow

### Generating Tokens

**AI Message**:
```
I've prepared a transaction for $500. 
To confirm, please type: CONFIRM-abc123
```

**Customer Response**:
```
CONFIRM-abc123
```

**AI Extracts Token**:
```python
import re

def extract_confirmation_token(message: str) -> str:
    """Extract confirmation token from customer message"""
    pattern = r'CONFIRM-[a-zA-Z0-9]+'
    match = re.search(pattern, message.upper())
    if match:
        return match.group(0)
    return None
```

---

## Permission Validation

### Context-Based Permissions

```python
async def validate_tool_permission(
    tool_name: str,
    user: User,
    conversation: Conversation
) -> bool:
    """Validate if user can use tool in this conversation"""
    
    # Check conversation access
    if not can_access_conversation(user, conversation):
        return False
    
    # Tool-specific rules
    if tool_name in ['create_transaction_draft', 'commit_transaction']:
        # Must be in Sales team
        sales_team_id = await get_team_id_by_slug('sales')
        if sales_team_id not in user.team_ids:
            await audit_log_denial(
                user, tool_name, conversation,
                reason="not_in_sales_team"
            )
            return False
    
    return True
```

---

## Rate Limiting

### Per-Conversation Limits

**Redis Implementation**:
```python
async def check_rate_limit(
    tool_name: str,
    conversation_id: str
) -> bool:
    """Check if rate limit exceeded"""
    
    limits = {
        'search_tickets': 20,
        'get_transaction_status': 30,
        'create_transaction_draft': 10,
        'commit_transaction': 5
    }
    
    limit = limits.get(tool_name, 50)
    key = f"rate_limit:{tool_name}:{conversation_id}"
    
    # Increment counter
    count = await redis.incr(key)
    
    # Set expiry on first call
    if count == 1:
        await redis.expire(key, 3600)  # 1 hour
    
    if count > limit:
        raise RateLimitExceededError(
            f"Rate limit exceeded for {tool_name}: {limit}/hour"
        )
    
    return True
```

---

## Input Sanitization

### Allowlist Pattern

```python
def sanitize_metadata(metadata: Dict, allowed_fields: List[str]) -> Dict:
    """Keep only allowed fields"""
    return {
        k: v for k, v in metadata.items()
        if k in allowed_fields
    }

# Usage
clean_metadata = sanitize_metadata(
    user_metadata,
    allowed_fields=['product_id', 'quantity', 'notes']
)
```

### Type Validation

```python
from pydantic import BaseModel, Field, validator

class TransactionDraftInput(BaseModel):
    customer_id: str
    amount: float = Field(gt=0, le=10000)
    description: str = Field(min_length=1, max_length=500)
    metadata: Dict = {}
    
    @validator('description')
    def validate_description(cls, v):
        # Block suspicious patterns
        suspicious = ['<script>', 'DROP TABLE', 'DELETE FROM']
        if any(pattern in v.upper() for pattern in suspicious):
            raise ValueError("Invalid description")
        return v
```

---

## PII Redaction

### Redact Sensitive Data from Logs

```python
import re

def redact_pii(text: str) -> str:
    """Redact PII from text"""
    
    # Email
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                  '***EMAIL***', text)
    
    # Phone (simple pattern)
    text = re.sub(r'\b\d{10,15}\b', '***PHONE***', text)
    
    # Credit card (simple pattern)
    text = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', 
                  '***CARD***', text)
    
    return text

# Usage in audit log
audit_log.info(
    "tool_called",
    tool_name="create_transaction_draft",
    input_params=redact_pii(json.dumps(params)),
    conversation_id=conversation_id
)
```

---

## Audit Logging

### Log Every Tool Call

```python
async def audit_tool_call(
    tool_name: str,
    input_params: Dict,
    output_result: Dict,
    status: str,
    conversation_id: str,
    user_id: str,
    denial_reason: str = None
):
    """Audit tool invocation"""
    
    await AIToolAuditLog.create(
        conversation_id=conversation_id,
        tool_name=tool_name,
        input_params=redact_pii(json.dumps(input_params)),
        output_result=redact_pii(json.dumps(output_result)) if output_result else None,
        status=status,  # success | failed | denied
        denial_reason=denial_reason,
        executed_by=f"agent:{user_id}"
    )
```

### Query Audit Logs

```python
# Get all tool calls for conversation
logs = await AIToolAuditLog.filter(
    conversation_id=conversation_id
).order_by('-created_at')

# Get denied calls (security review)
denied = await AIToolAuditLog.filter(
    status='denied'
).order_by('-created_at').limit(100)
```

---

## Guardrails

### Amount Thresholds

```python
AMOUNT_THRESHOLDS = {
    'auto_approve': 1000,      # AI can auto-commit
    'supervisor_approve': 5000, # Requires supervisor
    'admin_approve': 10000      # Max allowed
}

async def check_amount_approval(amount: float, user: User) -> bool:
    """Check if amount requires approval"""
    
    if amount <= AMOUNT_THRESHOLDS['auto_approve']:
        return True
    
    if amount <= AMOUNT_THRESHOLDS['supervisor_approve']:
        return user.role in ['supervisor', 'admin']
    
    if amount <= AMOUNT_THRESHOLDS['admin_approve']:
        return user.role == 'admin'
    
    raise ValueError(f"Amount exceeds maximum: ${AMOUNT_THRESHOLDS['admin_approve']}")
```

### Suspicious Pattern Detection

```python
async def detect_suspicious_activity(
    conversation_id: str,
    tool_name: str
) -> bool:
    """Detect suspicious patterns"""
    
    # Check for rapid-fire tool calls
    recent_calls = await AIToolAuditLog.filter(
        conversation_id=conversation_id,
        created_at__gte=now() - timedelta(minutes=5)
    ).count()
    
    if recent_calls > 10:
        await alert_supervisor(
            conversation_id,
            "Suspicious: 10+ tool calls in 5 minutes"
        )
        return True
    
    # Check for repeated failed confirmations
    failed_commits = await AIToolAuditLog.filter(
        conversation_id=conversation_id,
        tool_name='commit_transaction',
        status='failed',
        created_at__gte=now() - timedelta(hours=1)
    ).count()
    
    if failed_commits > 3:
        await alert_supervisor(
            conversation_id,
            "Suspicious: 3+ failed transaction commits"
        )
        return True
    
    return False
```

---

## Example: End-to-End Tool Call

### Scenario: AI creates transaction

```python
# 1. AI decides to create transaction
tool_request = {
    "tool": "create_transaction_draft",
    "params": {
        "customer_id": "uuid",
        "amount": 500.00,
        "description": "Premium plan purchase"
    }
}

# 2. Gateway validates
await validate_tool_permission("create_transaction_draft", user, conversation)
await check_rate_limit("create_transaction_draft", conversation.id)

# 3. Sanitize inputs
validated_params = TransactionDraftInput(**tool_request["params"])

# 4. Execute tool
result = await create_transaction_draft(**validated_params.dict())

# 5. Audit log
await audit_tool_call(
    tool_name="create_transaction_draft",
    input_params=validated_params.dict(),
    output_result=result,
    status="success",
    conversation_id=conversation.id,
    user_id=user.id
)

# 6. Return to AI
return result
```

---

**Next**: See [Observability](./08-observability.md) for logging and monitoring.
