# E. RBAC & Permissions

## Roles

### Role Hierarchy

```
Admin
  └─ Supervisor
      └─ Team Lead
          └─ Agent
```

**Inheritance**: Higher roles inherit all permissions from lower roles.

---

## Role Definitions

### Admin
- **Scope**: Global (all teams)
- **Purpose**: System configuration, user management
- **Count**: 2-5 users

**Capabilities**:
- Manage users (create, edit, deactivate)
- Manage teams (create, edit)
- Assign roles
- View all conversations across teams
- Configure integrations
- Access all reports and analytics
- Manage tags (global)

---

### Supervisor
- **Scope**: One or more teams
- **Purpose**: Team oversight, quality assurance
- **Count**: 5-10 users

**Capabilities**:
- View all conversations in assigned teams
- Assign conversations to agents
- Transfer conversations between teams
- Close any conversation in team
- View team metrics and reports
- Manage team-specific tags
- Access internal chat

---

### Team Lead (TL)
- **Scope**: Single team
- **Purpose**: Day-to-day team management
- **Count**: 10-20 users

**Capabilities**:
- View all conversations in own team
- Assign conversations to agents in team
- Transfer conversations within team
- Close conversations in team
- View team metrics
- Handle escalations
- Access internal chat

---

### Agent
- **Scope**: Assigned conversations only
- **Purpose**: Handle customer conversations
- **Count**: 150-180 users

**Capabilities**:
- View assigned conversations
- Take conversations from team queue
- Send messages to customers
- Add tags and notes to assigned conversations
- Close assigned conversations
- Access internal chat
- View own performance metrics

---

## Permission Matrix

| Permission | Admin | Supervisor | Team Lead | Agent |
|------------|-------|------------|-----------|-------|
| **Users & Teams** |
| Create/edit users | ✅ | ❌ | ❌ | ❌ |
| View all users | ✅ | ✅ (team) | ✅ (team) | ❌ |
| Assign roles | ✅ | ❌ | ❌ | ❌ |
| Create/edit teams | ✅ | ❌ | ❌ | ❌ |
| **Conversations** |
| View all conversations | ✅ | ✅ (team) | ✅ (team) | ❌ |
| View assigned conversations | ✅ | ✅ | ✅ | ✅ |
| Take from queue | ✅ | ✅ | ✅ | ✅ |
| Assign to agent | ✅ | ✅ (team) | ✅ (team) | ❌ |
| Transfer to team | ✅ | ✅ | ✅ (own team) | ❌ |
| Close conversation | ✅ | ✅ (team) | ✅ (team) | ✅ (assigned) |
| Reopen conversation | ✅ | ✅ (team) | ✅ (team) | ❌ |
| **Messages** |
| Send message | ✅ | ✅ | ✅ | ✅ (assigned) |
| View message history | ✅ | ✅ (team) | ✅ (team) | ✅ (assigned) |
| **Tags & Notes** |
| Create global tags | ✅ | ❌ | ❌ | ❌ |
| Create team tags | ✅ | ✅ | ✅ | ❌ |
| Add tags to conversation | ✅ | ✅ | ✅ | ✅ (assigned) |
| Add notes | ✅ | ✅ | ✅ | ✅ (assigned) |
| View notes | ✅ | ✅ (team) | ✅ (team) | ✅ (assigned) |
| **Internal Chat** |
| Create thread | ✅ | ✅ | ✅ | ✅ |
| Send message | ✅ | ✅ | ✅ | ✅ |
| **Reports** |
| View all team reports | ✅ | ✅ (assigned teams) | ✅ (own team) | ❌ |
| View agent reports | ✅ | ✅ (team agents) | ✅ (team agents) | ✅ (own) |
| Export data | ✅ | ✅ | ❌ | ❌ |
| **Integrations** |
| Configure integrations | ✅ | ❌ | ❌ | ❌ |
| View integration logs | ✅ | ✅ | ❌ | ❌ |
| **AI Tools** |
| Use AI tools | ✅ | ✅ | ✅ | ✅ (assigned) |
| View AI audit logs | ✅ | ✅ (team) | ✅ (team) | ❌ |

---

## Scoping Rules

### Team Scoping

**Rule**: Users can only access conversations in teams they belong to.

**Implementation**:
```python
def get_accessible_conversations(user):
    if user.role == 'admin':
        return Conversation.objects.all()
    
    team_ids = user.team_memberships.values_list('team_id', flat=True)
    
    if user.role in ['supervisor', 'team_lead']:
        return Conversation.objects.filter(team_id__in=team_ids)
    
    if user.role == 'agent':
        return Conversation.objects.filter(assigned_to=user.id)
```

---

### Conversation Scoping

**Agent Rule**: Can only view/edit conversations assigned to them.

**Exception**: Can view conversations in queue (read-only) to decide which to take.

**Implementation**:
```python
def can_access_conversation(user, conversation):
    # Admin: always
    if user.role == 'admin':
        return True
    
    # Must be in same team
    if conversation.team_id not in user.team_ids:
        return False
    
    # Supervisor/TL: any in team
    if user.role in ['supervisor', 'team_lead']:
        return True
    
    # Agent: only assigned or queued
    if user.role == 'agent':
        return (
            conversation.assigned_to == user.id or
            conversation.status == 'queued'
        )
    
    return False
```

---

### Message Scoping

**Rule**: Can only send messages to conversations you can access.

**WhatsApp Constraint**: Only assigned agent can send (to avoid confusion).

**Implementation**:
```python
def can_send_message(user, conversation):
    if not can_access_conversation(user, conversation):
        return False
    
    # For WhatsApp, only assigned agent
    if conversation.channel == 'whatsapp':
        return conversation.assigned_to == user.id
    
    # For chat app, any team member
    return user.role in ['admin', 'supervisor', 'team_lead'] or \
           conversation.assigned_to == user.id
```

---

## API Authorization

### JWT Token Structure

```json
{
  "sub": "user_uuid",
  "email": "agent@example.com",
  "role": "agent",
  "team_ids": ["sales_uuid", "support_uuid"],
  "exp": 1704470400
}
```

**Issued By**: `POST /auth/login`
**Expires**: 8 hours
**Refresh**: `POST /auth/refresh` (30-day refresh token)

---

### Endpoint Protection

**Decorator Pattern**:
```python
from functools import wraps
from fastapi import HTTPException, Depends

def require_role(min_role: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            role_hierarchy = ['agent', 'team_lead', 'supervisor', 'admin']
            if role_hierarchy.index(current_user.role) < role_hierarchy.index(min_role):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# Usage
@app.post("/users")
@require_role("admin")
async def create_user(data: UserCreate, current_user: User):
    ...
```

---

### Resource-Level Authorization

**Example**: Assign conversation

```python
@app.post("/conversations/{conversation_id}/assign")
async def assign_conversation(
    conversation_id: UUID,
    data: AssignRequest,
    current_user: User = Depends(get_current_user)
):
    conversation = await get_conversation(conversation_id)
    
    # Check team access
    if current_user.role != 'admin':
        if conversation.team_id not in current_user.team_ids:
            raise HTTPException(403, "Not in conversation's team")
    
    # Check role permission
    if current_user.role not in ['admin', 'supervisor', 'team_lead']:
        raise HTTPException(403, "Only supervisors/TLs can assign")
    
    # Validate target agent
    target_agent = await get_user(data.assigned_to)
    if conversation.team_id not in target_agent.team_ids:
        raise HTTPException(400, "Agent not in conversation's team")
    
    # Perform assignment
    await assign_conversation_to_agent(conversation, target_agent)
    return {"status": "assigned"}
```

---

## AI Tool Permissions

### Tool Access by Role

| Tool | Admin | Supervisor | Team Lead | Agent |
|------|-------|------------|-----------|-------|
| `search_tickets` | ✅ | ✅ | ✅ | ✅ |
| `get_transaction_status` | ✅ | ✅ | ✅ | ✅ |
| `create_transaction_draft` | ✅ | ✅ (Sales) | ✅ (Sales) | ✅ (Sales) |
| `commit_transaction` | ✅ | ✅ (Sales) | ✅ (Sales) | ✅ (Sales) |

**Sales Team Only**: Transaction creation restricted to Sales team members.

**Implementation**:
```python
def can_use_tool(user, tool_name, conversation):
    # Basic access check
    if not can_access_conversation(user, conversation):
        return False
    
    # Tool-specific rules
    if tool_name in ['create_transaction_draft', 'commit_transaction']:
        # Must be in Sales team
        sales_team_id = get_team_id_by_slug('sales')
        return sales_team_id in user.team_ids
    
    return True
```

---

## Audit Requirements

**Log All Permission Checks**:
```python
audit_log.info(
    "permission_check",
    user_id=user.id,
    resource_type="conversation",
    resource_id=conversation.id,
    action="assign",
    granted=True
)
```

**Failed Attempts**:
```python
audit_log.warning(
    "permission_denied",
    user_id=user.id,
    resource_type="conversation",
    resource_id=conversation.id,
    action="assign",
    reason="not_in_team"
)
```

---

## Special Cases

### Cross-Team Transfer

**Scenario**: Supervisor in Sales wants to transfer to Support.

**Rule**: Supervisor must be in BOTH teams, OR be Admin.

**Implementation**:
```python
def can_transfer_to_team(user, conversation, target_team_id):
    if user.role == 'admin':
        return True
    
    # Must be in source team
    if conversation.team_id not in user.team_ids:
        return False
    
    # Must be in target team (for non-admins)
    if target_team_id not in user.team_ids:
        return False
    
    return user.role in ['supervisor', 'team_lead']
```

---

### Emergency Access

**Scenario**: Admin needs to access conversation outside their teams.

**Rule**: Always allowed, but logged.

**Implementation**:
```python
if user.role == 'admin':
    audit_log.warning(
        "admin_override",
        user_id=user.id,
        conversation_id=conversation.id,
        reason="emergency_access"
    )
    return True
```

---

**Next**: See [API Contract](./05-api-contract.md) for endpoint specifications.
