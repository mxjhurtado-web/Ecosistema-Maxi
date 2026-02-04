# 📚 Usage Examples - ORBIT Integration

Complete examples for integrating the middleware with Respond.io and other platforms.

---

## 🎯 Respond.io Integration

### Step 1: Configure Webhook in Respond.io

1. **Login to Respond.io**
2. **Navigate to Settings → Webhooks**
3. **Click "Add Webhook"**

**Configuration:**
```
Name: MCP Middleware
URL: https://your-domain.com/webhook
Method: POST
Headers:
  X-Webhook-Secret: your-super-secret-key
Events:
  ☑ Message Received
```

### Step 2: Test Integration

Send a message in Respond.io and verify:
- Message appears in Dashboard → History
- Response is sent back to user
- Metrics updated in Dashboard → KPIs

---

## 💬 Example Conversations

### Example 1: News Query

**User (WhatsApp):**
```
noticias de tecnología
```

**Middleware Flow:**
1. Respond.io sends POST to `/webhook`
2. Middleware extracts "noticias de tecnología"
3. Queries MCP: `POST /query`
4. MCP returns news from Google News RSS
5. Middleware returns to Respond.io
6. User receives news in WhatsApp

**Response:**
```
📰 Últimas Noticias de Tecnología:

1. **Apple lanza nuevo iPhone 16**
   Fecha: 2026-02-04
   Fuente: TechCrunch
   🔗 https://...

2. **Google anuncia Gemini 2.0**
   Fecha: 2026-02-04
   Fuente: The Verge
   🔗 https://...

3. **Tesla presenta nuevo modelo**
   Fecha: 2026-02-03
   Fuente: Reuters
   🔗 https://...
```

### Example 2: General Query

**User:**
```
hola
```

**Response:**
```
¡Hola! Soy el asistente MCP. Puedo ayudarte con:
- Noticias de cualquier tema
- Últimas noticias

Ejemplos:
- "noticias de tecnología"
- "noticias de deportes"
- "últimas noticias"
```

### Example 3: Help Query

**User:**
```
ayuda
```

**Response:**
```
Puedo ayudarte con:
- Noticias de cualquier tema
- Últimas noticias

Ejemplos:
- 'noticias de tecnología'
- 'noticias de deportes'
- 'últimas noticias'
```

---

## 🔧 API Examples

### Example 1: Direct Webhook Call

```bash
curl -X POST https://your-domain.com/webhook \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your-secret" \
  -d '{
    "conversation_id": "conv_abc123",
    "contact_id": "contact_xyz789",
    "channel": "whatsapp",
    "user_text": "noticias de tecnología",
    "metadata": {
      "user_name": "John Doe",
      "user_phone": "+1234567890"
    }
  }'
```

**Response:**
```json
{
  "status": "ok",
  "response": "📰 Últimas Noticias de Tecnología:\n\n1. ...",
  "latency_ms": 1234,
  "trace_id": "abc-123-def-456",
  "retry_count": 0,
  "mcp_latency_ms": 1100
}
```

### Example 2: Health Check

```bash
curl https://your-domain.com/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-04T15:30:00Z",
  "mcp_status": "healthy",
  "redis_status": "healthy"
}
```

### Example 3: Admin API - Get Config

```bash
curl "https://your-domain.com/admin/config/mcp?username=admin&password=your-password"
```

**Response:**
```json
{
  "url": "http://mcp:8080/query",
  "timeout": 5,
  "max_retries": 3,
  "retry_delay": 1
}
```

### Example 4: Admin API - Update Config

```bash
curl -X PUT "https://your-domain.com/admin/config/mcp?username=admin&password=your-password" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://new-mcp:8080/query",
    "timeout": 10,
    "max_retries": 5,
    "retry_delay": 2
  }'
```

---

## 🌐 Multi-Channel Examples

### WhatsApp

```json
{
  "conversation_id": "whatsapp_conv_123",
  "contact_id": "whatsapp_contact_456",
  "channel": "whatsapp",
  "user_text": "noticias de deportes",
  "metadata": {
    "phone": "+1234567890",
    "name": "John Doe"
  }
}
```

### Telegram

```json
{
  "conversation_id": "telegram_conv_123",
  "contact_id": "telegram_contact_456",
  "channel": "telegram",
  "user_text": "últimas noticias",
  "metadata": {
    "username": "@johndoe",
    "chat_id": "123456789"
  }
}
```

### Facebook Messenger

```json
{
  "conversation_id": "messenger_conv_123",
  "contact_id": "messenger_contact_456",
  "channel": "messenger",
  "user_text": "noticias de tecnología",
  "metadata": {
    "page_id": "123456789",
    "sender_id": "987654321"
  }
}
```

---

## 🔄 Error Handling Examples

### Example 1: MCP Timeout

**Request:**
```json
{
  "user_text": "test query"
}
```

**Response (after 3 retries):**
```json
{
  "status": "error",
  "response": "Lo siento, no pude procesar tu solicitud en este momento. Por favor intenta nuevamente.",
  "latency_ms": 15000,
  "trace_id": "abc-123",
  "retry_count": 3,
  "error_message": "MCP timeout"
}
```

### Example 2: Circuit Breaker Open

**Response:**
```json
{
  "status": "error",
  "response": "Lo siento, el servicio está temporalmente no disponible. Por favor intenta más tarde.",
  "latency_ms": 0,
  "trace_id": "abc-123",
  "retry_count": 0
}
```

### Example 3: Invalid Secret

**Response:**
```
HTTP 401 Unauthorized
{
  "detail": "Invalid webhook secret"
}
```

---

## 📊 Dashboard Usage Examples

### Example 1: View Request Details

1. Open Dashboard → History
2. Search for trace_id: `abc-123-def`
3. Click to expand request
4. View:
   - User text
   - MCP response
   - Latency metrics
   - Retry count
   - Error details (if any)

### Example 2: Update MCP Configuration

1. Open Dashboard → Configuration
2. Go to "MCP Settings" tab
3. Update URL: `http://new-mcp:8080/query`
4. Update timeout: `10` seconds
5. Click "Test Connection"
6. If successful, click "Save Configuration"

### Example 3: Test with Chat

1. Open Dashboard → Chat
2. Select channel: "whatsapp"
3. Type: "noticias de tecnología"
4. Press Enter
5. View response with metrics:
   - Latency: 1234ms
   - Status: ok
   - Retries: 0

### Example 4: Export Request History

1. Open Dashboard → History
2. Filter by date range
3. Search for specific queries
4. Click "Download CSV"
5. Open in Excel/Google Sheets

---

## 🧪 Testing Scenarios

### Scenario 1: Load Testing

```bash
# Install Apache Bench
apt-get install apache2-utils

# Run load test
ab -n 1000 -c 10 \
  -H "X-Webhook-Secret: your-secret" \
  -H "Content-Type: application/json" \
  -p request.json \
  https://your-domain.com/webhook
```

**request.json:**
```json
{
  "conversation_id": "load_test",
  "contact_id": "test_contact",
  "channel": "whatsapp",
  "user_text": "test message"
}
```

### Scenario 2: Circuit Breaker Testing

```bash
# Stop MCP server
docker-compose stop mock_mcp

# Send 6 requests (threshold is 5)
for i in {1..6}; do
  curl -X POST http://localhost:8000/webhook \
    -H "X-Webhook-Secret: your-secret" \
    -H "Content-Type: application/json" \
    -d '{"conversation_id":"test","contact_id":"test","channel":"whatsapp","user_text":"test"}'
done

# Circuit should be open now
# Check in Dashboard → Maintenance → Circuit Breaker
```

### Scenario 3: Cache Testing

```bash
# Send same query twice
curl -X POST http://localhost:8000/webhook \
  -H "X-Webhook-Secret: your-secret" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id":"test1","contact_id":"test","channel":"whatsapp","user_text":"noticias de tecnología"}'

# Second request should be faster (cached)
curl -X POST http://localhost:8000/webhook \
  -H "X-Webhook-Secret: your-secret" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id":"test2","contact_id":"test","channel":"whatsapp","user_text":"noticias de tecnología"}'
```

---

## 🔗 Integration with Other Platforms

### Make.com (Integromat)

1. Create new scenario
2. Add HTTP module
3. Configure:
   ```
   URL: https://your-domain.com/webhook
   Method: POST
   Headers:
     X-Webhook-Secret: your-secret
   Body:
     {
       "conversation_id": "{{conversation_id}}",
       "contact_id": "{{contact_id}}",
       "channel": "make",
       "user_text": "{{user_message}}"
     }
   ```

### Zapier

1. Create new Zap
2. Add Webhooks by Zapier
3. Choose "POST"
4. Configure:
   ```
   URL: https://your-domain.com/webhook
   Payload Type: JSON
   Data:
     conversation_id: {{conversation_id}}
     contact_id: {{contact_id}}
     channel: zapier
     user_text: {{user_message}}
   Headers:
     X-Webhook-Secret: your-secret
   ```

### n8n

```json
{
  "nodes": [
    {
      "name": "HTTP Request",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "https://your-domain.com/webhook",
        "method": "POST",
        "headerParameters": {
          "parameters": [
            {
              "name": "X-Webhook-Secret",
              "value": "your-secret"
            }
          ]
        },
        "bodyParameters": {
          "parameters": [
            {
              "name": "conversation_id",
              "value": "={{$json.conversation_id}}"
            },
            {
              "name": "user_text",
              "value": "={{$json.message}}"
            }
          ]
        }
      }
    }
  ]
}
```

---

## 📝 Best Practices

### 1. **Use Trace IDs for Debugging**

Always save the `trace_id` from responses:
```json
{
  "trace_id": "abc-123-def-456"
}
```

Search in Dashboard → History to find the exact request.

### 2. **Monitor Success Rate**

Keep success rate > 95%:
- Check Dashboard → KPIs
- If < 95%, investigate errors
- Check MCP health

### 3. **Set Up Alerts**

Monitor:
- Success rate drops below 95%
- Latency > 5 seconds
- Circuit breaker opens
- Error rate spikes

### 4. **Regular Backups**

Backup Redis data daily:
```bash
docker-compose exec redis redis-cli SAVE
docker cp respondio_redis:/data/dump.rdb ./backup.rdb
```

---

**Ready to integrate!** 🚀
