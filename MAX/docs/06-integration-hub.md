# G. Integration Hub

## Overview

The **Integration Hub** is a centralized adapter layer that connects MAX to external systems. It provides:
- Unified interface for external API calls
- Error handling and retry logic
- Caching for read operations
- Circuit breaker pattern
- Audit logging

---

## Architecture

```
┌──────────────────────────────────────────────────┐
│              Integration Hub                      │
├──────────────────────────────────────────────────┤
│                                                   │
│  ┌─────────────────┐  ┌─────────────────┐       │
│  │ Ticketing       │  │ Transaction     │       │
│  │ Adapter         │  │ Status Adapter  │       │
│  └────────┬────────┘  └────────┬────────┘       │
│           │                    │                 │
│  ┌────────┴────────────────────┴────────┐       │
│  │   Transaction Create Adapter         │       │
│  └──────────────────────────────────────┘       │
│                                                   │
│  ┌──────────────────────────────────────┐       │
│  │   Common Services                    │       │
│  ├──────────────────────────────────────┤       │
│  │ • Retry Handler                      │       │
│  │ • Circuit Breaker                    │       │
│  │ • Cache Manager                      │       │
│  │ • Secrets Manager                    │       │
│  │ • Audit Logger                       │       │
│  └──────────────────────────────────────┘       │
└──────────────────────────────────────────────────┘
```

---

## Adapter Pattern

### Base Adapter

```python
from abc import ABC, abstractmethod
from typing import Any, Dict
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

class BaseAdapter(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = httpx.AsyncClient(timeout=10.0)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60
        )
    
    @abstractmethod
    async def authenticate(self) -> str:
        """Return auth token/header"""
        pass
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        
        if self.circuit_breaker.is_open():
            raise CircuitBreakerOpenError("Circuit breaker is open")
        
        try:
            auth_header = await self.authenticate()
            headers = kwargs.get('headers', {})
            headers.update(auth_header)
            
            response = await self.client.request(
                method,
                f"{self.config['base_url']}{endpoint}",
                headers=headers,
                **kwargs
            )
            response.raise_for_status()
            
            self.circuit_breaker.record_success()
            return response.json()
            
        except httpx.HTTPError as e:
            self.circuit_breaker.record_failure()
            await self._log_error(method, endpoint, e)
            raise
    
    async def _log_error(self, method: str, endpoint: str, error: Exception):
        """Log integration error"""
        await IntegrationLog.create(
            integration_name=self.__class__.__name__,
            operation=f"{method} {endpoint}",
            error=str(error),
            status_code=getattr(error, 'status_code', None)
        )
```

---

## 1. Ticketing Adapter

### Purpose
Create and manage support tickets in external ticketing system (e.g., Zendesk, Jira).

### Configuration
```json
{
  "base_url": "https://tickets.example.com/api/v2",
  "auth_type": "api_key",
  "api_key": "encrypted_key_from_secrets_manager"
}
```

### Operations

#### create_ticket
```python
async def create_ticket(
    self,
    customer_id: str,
    subject: str,
    description: str,
    priority: str = "normal"
) -> Dict[str, Any]:
    """
    Create support ticket.
    
    Returns:
        {
            "ticket_id": "TICKET-123",
            "url": "https://tickets.example.com/tickets/123",
            "status": "open"
        }
    """
    payload = {
        "subject": subject,
        "description": description,
        "priority": priority,
        "custom_fields": {
            "customer_id": customer_id
        }
    }
    
    result = await self._request(
        "POST",
        "/tickets",
        json=payload
    )
    
    return {
        "ticket_id": result["id"],
        "url": result["url"],
        "status": result["status"]
    }
```

#### get_ticket_status
```python
@cached(ttl=300)  # Cache 5 minutes
async def get_ticket_status(self, ticket_id: str) -> Dict[str, Any]:
    """
    Get ticket status.
    
    Returns:
        {
            "ticket_id": "TICKET-123",
            "status": "in_progress",
            "assigned_to": "support@example.com",
            "last_updated": "2026-01-05T12:00:00Z"
        }
    """
    result = await self._request("GET", f"/tickets/{ticket_id}")
    
    return {
        "ticket_id": result["id"],
        "status": result["status"],
        "assigned_to": result.get("assignee", {}).get("email"),
        "last_updated": result["updated_at"]
    }
```

#### add_comment
```python
async def add_comment(
    self,
    ticket_id: str,
    comment: str,
    is_public: bool = True
) -> Dict[str, Any]:
    """Add comment to ticket"""
    payload = {
        "body": comment,
        "public": is_public
    }
    
    result = await self._request(
        "POST",
        f"/tickets/{ticket_id}/comments",
        json=payload
    )
    
    return {"comment_id": result["id"]}
```

---

## 2. Transaction Status Adapter

### Purpose
Query transaction status from payment/order system.

### Configuration
```json
{
  "base_url": "https://transactions.example.com/api/v1",
  "auth_type": "oauth2",
  "client_id": "encrypted_client_id",
  "client_secret": "encrypted_client_secret"
}
```

### Authentication
```python
async def authenticate(self) -> Dict[str, str]:
    """OAuth2 client credentials flow"""
    if self._token_valid():
        return {"Authorization": f"Bearer {self._cached_token}"}
    
    response = await self.client.post(
        f"{self.config['base_url']}/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": self.config['client_id'],
            "client_secret": self.config['client_secret']
        }
    )
    
    token_data = response.json()
    self._cached_token = token_data["access_token"]
    self._token_expires_at = now() + timedelta(seconds=token_data["expires_in"])
    
    return {"Authorization": f"Bearer {self._cached_token}"}
```

### Operations

#### get_transaction_status
```python
@cached(ttl=120)  # Cache 2 minutes
async def get_transaction_status(self, transaction_id: str) -> Dict[str, Any]:
    """
    Get transaction status.
    
    Returns:
        {
            "transaction_id": "TXN-12345",
            "status": "completed",
            "amount": 500.00,
            "currency": "USD",
            "created_at": "2026-01-05T10:00:00Z",
            "completed_at": "2026-01-05T10:05:00Z"
        }
    """
    result = await self._request("GET", f"/transactions/{transaction_id}")
    
    return {
        "transaction_id": result["id"],
        "status": result["status"],
        "amount": result["amount"],
        "currency": result["currency"],
        "created_at": result["created_at"],
        "completed_at": result.get("completed_at")
    }
```

#### get_transaction_history
```python
@cached(ttl=300)
async def get_transaction_history(
    self,
    customer_id: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Get customer transaction history"""
    result = await self._request(
        "GET",
        f"/customers/{customer_id}/transactions",
        params={"limit": limit}
    )
    
    return [
        {
            "transaction_id": txn["id"],
            "amount": txn["amount"],
            "status": txn["status"],
            "created_at": txn["created_at"]
        }
        for txn in result["transactions"]
    ]
```

---

## 3. Transaction Create Adapter

### Purpose
Create new transactions (sales orders, payments).

### Configuration
```json
{
  "base_url": "https://sales.example.com/api/v1",
  "auth_type": "oauth2_hmac",
  "client_id": "encrypted_client_id",
  "client_secret": "encrypted_client_secret",
  "hmac_secret": "encrypted_hmac_secret"
}
```

### Operations

#### create_draft_transaction
```python
async def create_draft_transaction(
    self,
    customer_id: str,
    amount: float,
    description: str,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Create draft transaction (not committed).
    
    Returns:
        {
            "draft_id": "DRAFT-abc123",
            "status": "pending_confirmation",
            "amount": 500.00,
            "expires_at": "2026-01-05T12:30:00Z"
        }
    """
    payload = {
        "customer_id": customer_id,
        "amount": amount,
        "description": description,
        "metadata": metadata or {},
        "status": "draft"
    }
    
    # Add HMAC signature
    signature = self._generate_hmac(payload)
    headers = {"X-HMAC-Signature": signature}
    
    result = await self._request(
        "POST",
        "/transactions/drafts",
        json=payload,
        headers=headers
    )
    
    return {
        "draft_id": result["id"],
        "status": result["status"],
        "amount": result["amount"],
        "expires_at": result["expires_at"]
    }
```

#### commit_transaction
```python
async def commit_transaction(
    self,
    draft_id: str,
    idempotency_key: str
) -> Dict[str, Any]:
    """
    Commit draft transaction (finalize).
    
    Args:
        draft_id: Draft transaction ID
        idempotency_key: Unique key to prevent duplicate commits
    
    Returns:
        {
            "transaction_id": "TXN-12345",
            "status": "completed",
            "amount": 500.00
        }
    """
    payload = {"draft_id": draft_id}
    signature = self._generate_hmac(payload)
    
    headers = {
        "X-HMAC-Signature": signature,
        "Idempotency-Key": idempotency_key
    }
    
    result = await self._request(
        "POST",
        f"/transactions/drafts/{draft_id}/commit",
        json=payload,
        headers=headers
    )
    
    return {
        "transaction_id": result["id"],
        "status": result["status"],
        "amount": result["amount"]
    }
```

#### cancel_draft
```python
async def cancel_draft(self, draft_id: str) -> Dict[str, Any]:
    """Cancel draft transaction"""
    result = await self._request(
        "POST",
        f"/transactions/drafts/{draft_id}/cancel"
    )
    
    return {"status": "cancelled"}
```

---

## Error Handling

### Retry Strategy

| Error Type | Retry | Backoff |
|------------|-------|---------|
| Network timeout | 3 attempts | Exponential (2s, 4s, 8s) |
| 5xx server error | 3 attempts | Exponential |
| 429 rate limit | 3 attempts | Exponential |
| 4xx client error | No retry | - |
| 401 auth error | 1 retry (re-auth) | - |

### Circuit Breaker

**Parameters**:
- Failure threshold: 5 consecutive failures
- Recovery timeout: 60 seconds
- Half-open test: 1 request

**States**:
- **Closed**: Normal operation
- **Open**: All requests fail immediately
- **Half-Open**: Test request to check recovery

### Dead Letter Queue (DLQ)

**Failed Operations** → DLQ for manual review

**Example**:
```python
try:
    result = await adapter.create_ticket(...)
except Exception as e:
    await dlq.enqueue({
        "operation": "create_ticket",
        "payload": {...},
        "error": str(e),
        "timestamp": now()
    })
    
    # Notify supervisor
    await notify_supervisor(
        "Integration failure: Ticketing system unavailable"
    )
```

---

## Caching Strategy

### Cache Keys
```python
def cache_key(operation: str, params: Dict) -> str:
    """Generate cache key"""
    param_str = json.dumps(params, sort_keys=True)
    return f"integration:{operation}:{hashlib.md5(param_str.encode()).hexdigest()}"
```

### Cache Invalidation

**Webhook-based**:
```python
@app.post("/webhooks/transaction_updated")
async def handle_transaction_webhook(data: Dict):
    """Invalidate cache when transaction updates"""
    transaction_id = data["transaction_id"]
    
    # Invalidate cache
    await cache.delete(f"integration:get_transaction_status:{transaction_id}")
    
    # Notify relevant conversations
    conversations = await find_conversations_by_metadata(
        {"transaction_id": transaction_id}
    )
    
    for conv in conversations:
        await push_websocket_event(conv.assigned_to, {
            "event": "transaction.updated",
            "data": data
        })
```

---

## Observability

### Metrics

**Tracked per adapter**:
- Request count (success/failure)
- Latency (p50, p95, p99)
- Error rate
- Circuit breaker state
- Cache hit rate

**Example (Prometheus)**:
```python
integration_requests_total = Counter(
    'integration_requests_total',
    'Total integration requests',
    ['adapter', 'operation', 'status']
)

integration_latency_seconds = Histogram(
    'integration_latency_seconds',
    'Integration request latency',
    ['adapter', 'operation']
)
```

### Logging

**Structured logs**:
```python
logger.info(
    "integration_request",
    adapter="TicketingAdapter",
    operation="create_ticket",
    duration_ms=250,
    status="success",
    conversation_id="uuid"
)
```

---

## Security

### Secrets Management

**Use AWS Secrets Manager / HashiCorp Vault**:
```python
async def get_integration_config(name: str) -> Dict:
    """Fetch encrypted config from secrets manager"""
    secret = await secrets_manager.get_secret(f"max/integrations/{name}")
    return json.loads(secret)
```

**Never log secrets**:
```python
def sanitize_for_logging(data: Dict) -> Dict:
    """Remove sensitive fields"""
    sensitive_keys = ['api_key', 'client_secret', 'password', 'token']
    return {
        k: '***REDACTED***' if k in sensitive_keys else v
        for k, v in data.items()
    }
```

---

**Next**: See [AI Tool Gateway](./07-ai-gateway.md) for AI security layer.
