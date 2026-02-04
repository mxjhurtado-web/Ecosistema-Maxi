# 🔀 Multi-MCP Support - Future Enhancement

## Overview

The middleware is **prepared for multi-MCP support**, allowing you to connect multiple MCP servers and route requests intelligently.

## Current Status

✅ **Architecture Ready**
- Router system implemented
- Configuration models defined
- Routing rules framework in place

🔄 **Currently Using**
- Single MCP server (default)
- All requests go to the same MCP

## Future Multi-MCP Capabilities

### 1. Multiple MCP Servers

Configure multiple MCP servers:

```python
servers = [
    {
        "name": "news_mcp",
        "url": "http://news-mcp:8080/query",
        "tags": ["news", "media"],
        "priority": 100
    },
    {
        "name": "support_mcp",
        "url": "http://support-mcp:8080/query",
        "tags": ["support", "help"],
        "priority": 90
    },
    {
        "name": "general_mcp",
        "url": "http://general-mcp:8080/query",
        "tags": ["general"],
        "priority": 50
    }
]
```

### 2. Intelligent Routing

Route requests based on:

#### **Keyword-based Routing**
```python
# If user asks about "noticias" → route to news_mcp
{
    "condition_type": "keyword",
    "condition_value": "noticias",
    "target_mcp": "news_mcp"
}
```

#### **Channel-based Routing**
```python
# WhatsApp → support_mcp
# Telegram → general_mcp
{
    "condition_type": "channel",
    "condition_value": "whatsapp",
    "target_mcp": "support_mcp"
}
```

#### **Tag-based Routing**
```python
# Requests tagged with "urgent" → priority_mcp
{
    "condition_type": "tag",
    "condition_value": "urgent",
    "target_mcp": "priority_mcp"
}
```

### 3. Fallback Strategy

If primary MCP fails:
1. Try next MCP by priority
2. Use default MCP
3. Return fallback message

### 4. Load Balancing

Distribute requests across multiple MCPs:
- Round-robin
- Least connections
- Response time based

## Implementation Roadmap

### Phase 1: Basic Multi-MCP ✅ READY
- [x] Router architecture
- [x] Configuration models
- [x] Routing rules framework

### Phase 2: Dashboard Integration (Future)
- [ ] UI to add/remove MCP servers
- [ ] UI to create routing rules
- [ ] MCP health monitoring
- [ ] Per-MCP statistics

### Phase 3: Advanced Routing (Future)
- [ ] AI-based routing (ML model decides)
- [ ] A/B testing between MCPs
- [ ] Geographic routing
- [ ] Time-based routing

### Phase 4: Load Balancing (Future)
- [ ] Round-robin distribution
- [ ] Health-based routing
- [ ] Response time optimization

## How to Enable Multi-MCP (When Ready)

### 1. Add New MCP Server

```python
from api.mcp_router import mcp_router, MCPServerConfig

new_mcp = MCPServerConfig(
    name="news_mcp",
    url="http://news-mcp:8080/query",
    timeout=5,
    max_retries=3,
    enabled=True,
    priority=100,
    tags=["news", "media"],
    description="Specialized news MCP"
)

mcp_router.add_mcp(new_mcp)
```

### 2. Add Routing Rule

```python
from api.mcp_router import MCPRoutingRule

rule = MCPRoutingRule(
    name="news_routing",
    condition_type="keyword",
    condition_value="noticias",
    target_mcp="news_mcp",
    enabled=True
)

mcp_router.add_routing_rule(rule)
```

### 3. Query Routing

```python
# Router automatically selects the right MCP
mcp_config = mcp_router.get_mcp_for_request(
    user_text="últimas noticias de tecnología",
    channel="whatsapp",
    tags=["news"]
)

# Use the selected MCP
response = await query_mcp(mcp_config, user_text)
```

## Benefits of Multi-MCP

### 🎯 Specialization
- Dedicated MCP for news
- Dedicated MCP for support
- Dedicated MCP for general queries

### ⚡ Performance
- Distribute load across servers
- Reduce latency with specialized MCPs
- Scale horizontally

### 🛡️ Reliability
- Fallback to other MCPs if one fails
- No single point of failure
- Better uptime

### 📊 Flexibility
- A/B test different MCP implementations
- Gradual rollout of new MCPs
- Easy to add/remove MCPs

## Example Use Cases

### Use Case 1: Department-based Routing
```
Sales queries → sales_mcp
Support queries → support_mcp
General queries → general_mcp
```

### Use Case 2: Language-based Routing
```
Spanish queries → spanish_mcp
English queries → english_mcp
```

### Use Case 3: Priority-based Routing
```
VIP customers → premium_mcp (faster, better)
Regular customers → standard_mcp
```

### Use Case 4: Feature Testing
```
10% of traffic → experimental_mcp
90% of traffic → stable_mcp
```

## Dashboard Multi-MCP UI (Future)

### MCP Management Page
```
┌─────────────────────────────────────┐
│  MCP Servers                         │
├─────────────────────────────────────┤
│  ✅ news_mcp      [Edit] [Disable]  │
│  ✅ support_mcp   [Edit] [Disable]  │
│  ❌ test_mcp      [Edit] [Enable]   │
│                                      │
│  [+ Add New MCP Server]              │
└─────────────────────────────────────┘
```

### Routing Rules Page
```
┌─────────────────────────────────────┐
│  Routing Rules                       │
├─────────────────────────────────────┤
│  ✅ News Routing                     │
│     keyword: "noticias" → news_mcp   │
│     [Edit] [Disable]                 │
│                                      │
│  ✅ WhatsApp Support                 │
│     channel: "whatsapp" → support_mcp│
│     [Edit] [Disable]                 │
│                                      │
│  [+ Add New Rule]                    │
└─────────────────────────────────────┘
```

### MCP Statistics
```
┌─────────────────────────────────────┐
│  MCP Performance                     │
├─────────────────────────────────────┤
│  news_mcp                            │
│    Requests: 1,234                   │
│    Avg Latency: 850ms                │
│    Success Rate: 98.5%               │
│                                      │
│  support_mcp                         │
│    Requests: 567                     │
│    Avg Latency: 650ms                │
│    Success Rate: 99.2%               │
└─────────────────────────────────────┘
```

## Current Implementation

For now, the system uses a **single default MCP**:

```python
DEFAULT_MULTI_MCP_CONFIG = MultiMCPConfig(
    servers=[
        MCPServerConfig(
            name="default",
            url="http://localhost:8080/query",
            enabled=True,
            priority=100
        )
    ],
    default_mcp="default"
)
```

All requests are routed to this MCP. The architecture is ready for expansion when needed.

## Migration Path

When you're ready to add more MCPs:

1. ✅ Add new MCP server config
2. ✅ Create routing rules
3. ✅ Test with chat interface
4. ✅ Monitor performance
5. ✅ Adjust routing as needed

**No code changes required - just configuration!**
