# J. Roadmap & User Stories

## Implementation Phases

---

## MVP 1: Core Inbox (4-6 weeks)

### Goal
Basic omnichannel inbox with manual assignment and WhatsApp + Chat App support.

### Features

#### 1. Authentication & Users
- [x] User login/logout (JWT)
- [x] Role-based access (Admin, Supervisor, TL, Agent)
- [x] Team management
- [x] User profile

#### 2. Conversations & Messages
- [x] WhatsApp webhook ingestion
- [x] Chat App webhook ingestion
- [x] Message normalization
- [x] Conversation creation
- [x] Message display (inbox)
- [x] Send message to customer
- [x] WhatsApp 24h window handling

#### 3. Queue & Assignment
- [x] Team-based queues
- [x] Manual assignment (Supervisor → Agent)
- [x] "Take from queue" (Agent self-assign)
- [x] Conversation states (new/queued/assigned/closed)

#### 4. Basic UI
- [x] Login page
- [x] Inbox (list conversations)
- [x] Conversation view (messages)
- [x] Send message form
- [x] Queue view per team

#### 5. Infrastructure
- [x] PostgreSQL database
- [x] Redis cache
- [x] Celery workers (basic)
- [x] WebSocket for real-time updates

#### 6. Critical Enhancements
- [x] Media handling (images, videos, documents)
- [x] Canned responses / quick replies
- [x] Rate limiting (customer-side anti-spam)


### User Stories

**As an Agent**:
- ✅ I can log in and see my assigned conversations
- ✅ I can take a conversation from my team's queue
- ✅ I can send messages to customers (WhatsApp/Chat App)
- ✅ I can see when messages are delivered/read
- ✅ I can close conversations with a reason

**As a Supervisor**:
- ✅ I can see all conversations in my team
- ✅ I can assign conversations to agents
- ✅ I can view queue backlog
- ✅ I can close any conversation in my team

**As an Admin**:
- ✅ I can create users and assign roles
- ✅ I can create teams
- ✅ I can view all conversations across teams

### Acceptance Criteria

**WhatsApp Integration**:
- [ ] Webhook receives messages within 2 seconds
- [ ] Messages deduplicated (no duplicates)
- [ ] Delivery statuses tracked (sent/delivered/read)
- [ ] 24h window enforced (error if outside window)

**Performance**:
- [ ] Inbox loads < 1 second
- [ ] Message send < 500ms
- [ ] WebSocket updates < 200ms latency

**Security**:
- [ ] All endpoints require authentication
- [ ] Agents can only access assigned conversations
- [ ] Passwords hashed (bcrypt)

---

## MVP 2: Triage & Routing (3-4 weeks)

### Goal
Automated triage flow to route conversations to correct team.

### Features

#### 1. Triage Flow
- [x] Welcome message on first contact
- [x] Team selection (Sales/Support/Customer Service)
- [x] Context collection (minimal questions)
- [x] Routing decision
- [x] "I want a human" escape hatch

#### 2. Tags & Notes
- [x] Create tags (global and team-specific)
- [x] Add tags to conversations
- [x] Add internal notes
- [x] Pin important notes

#### 3. Metrics & Reporting
- [x] First Response Time (FRT) tracking
- [x] Resolution Time tracking
- [x] Queue backlog metrics
- [x] Agent performance dashboard
- [x] Team performance dashboard

#### 4. Internal Chat
- [x] Create agent-to-agent threads
- [x] Send messages in threads
- [x] Unread count
- [x] Notifications

#### 5. Important Enhancements
- [x] SLA management and escalations
- [x] Customer identity resolution (link WhatsApp + Chat App)
- [x] Business hours handling
- [x] WhatsApp templates CRUD


### User Stories

**As a Customer**:
- ✅ I receive a welcome message when I first contact
- ✅ I can select my issue type (Sales/Support/Service)
- ✅ I'm routed to the correct team
- ✅ I can say "I want a human" to skip triage

**As an Agent**:
- ✅ I can add tags to conversations for organization
- ✅ I can add internal notes (not visible to customer)
- ✅ I can chat with other agents for help
- ✅ I can see my performance metrics (FRT, resolution time)

**As a Supervisor**:
- ✅ I can view team metrics (FRT, backlog, etc.)
- ✅ I can see which agents are overloaded
- ✅ I can export reports

### Acceptance Criteria

**Triage Flow**:
- [ ] 90% of conversations routed correctly
- [ ] Triage completes in < 2 minutes
- [ ] "I want a human" triggers immediate escalation

**Metrics**:
- [ ] FRT calculated within 1 minute of first response
- [ ] Dashboards update in real-time
- [ ] Reports exportable as CSV

---

## MVP 3: Integrations & AI (4-6 weeks)

### Goal
External integrations and AI copilot for agents.

### Features

#### 1. Integration Hub
- [x] Ticketing adapter (create/view tickets)
- [x] Transaction status adapter (query status)
- [x] Transaction create adapter (draft/commit)
- [x] Retry logic and circuit breaker
- [x] Integration audit logs

#### 2. AI Tool Gateway
- [x] Tool definitions (search_tickets, get_transaction_status, etc.)
- [x] Permission validation
- [x] Rate limiting
- [x] Confirmation token flow (for transactions)
- [x] PII redaction
- [x] Audit logging

#### 3. AI Copilot
- [x] Suggest replies to agents
- [x] Summarize conversation history
- [x] Call tools on behalf of agent (with approval)
- [x] Auto-tag conversations

#### 4. Advanced Features
- [x] Transfer conversations between teams
- [x] Reopen closed conversations
- [x] Conversation search
- [x] Message templates (WhatsApp)

### User Stories

**As an Agent**:
- ✅ I can search for customer tickets without leaving MAX
- ✅ I can check transaction status inline
- ✅ I get AI-suggested replies to speed up responses
- ✅ I can transfer conversations to other teams

**As a Sales Agent**:
- ✅ I can create draft transactions
- ✅ I can commit transactions after customer confirms
- ✅ AI prevents me from creating invalid transactions

**As a Supervisor**:
- ✅ I can view all AI tool invocations for audit
- ✅ I can see denied tool calls (security review)
- ✅ I can approve high-value transactions

### Acceptance Criteria

**Integrations**:
- [ ] Tool calls complete in < 5 seconds
- [ ] Failed calls retry automatically (max 3 attempts)
- [ ] Circuit breaker opens after 5 failures

**AI Security**:
- [ ] AI never receives API keys
- [ ] All tool calls audited
- [ ] Transactions > $1000 require supervisor approval
- [ ] PII redacted from logs

---

## Future Enhancements (Post-MVP 3)

### Phase 4: Operational Excellence
- Skills-based routing
- Conversation merging (duplicate detection)
- AI confidence scores
- Customer context panel (unified history)
- Outbound webhooks

### Phase 5: Auto-Assignment
- Capacity-based agent assignment
- Load balancing
- Predictive routing

### Phase 6: Advanced AI
- Fully autonomous AI agent (with guardrails)
- Sentiment analysis
- Intent prediction
- Proactive suggestions

### Phase 7: Multi-Channel
- Email integration
- SMS integration
- Social media (Facebook, Instagram)

### Phase 8: Customer Portal
- Self-service knowledge base
- Conversation history for customers
- Rating/feedback system

### Phase 9: Advanced Analytics
- Predictive analytics (forecast volume)
- Agent coaching insights
- Customer journey mapping


---

## User Stories by Role

### Admin

**User Management**:
- As an Admin, I can create new users with specific roles
- As an Admin, I can deactivate users
- As an Admin, I can assign users to teams
- As an Admin, I can reset user passwords

**System Configuration**:
- As an Admin, I can configure integration credentials
- As an Admin, I can create global tags
- As an Admin, I can view system health metrics
- As an Admin, I can export audit logs

**Acceptance Criteria**:
- [ ] User creation takes < 5 seconds
- [ ] Deactivated users cannot log in
- [ ] Integration configs encrypted at rest

---

### Supervisor

**Team Oversight**:
- As a Supervisor, I can view all conversations in my teams
- As a Supervisor, I can see queue backlog per team
- As a Supervisor, I can view agent performance metrics
- As a Supervisor, I can identify overloaded agents

**Assignment & Transfer**:
- As a Supervisor, I can assign conversations to agents
- As a Supervisor, I can transfer conversations between teams
- As a Supervisor, I can close any conversation in my team
- As a Supervisor, I can reopen closed conversations

**Reporting**:
- As a Supervisor, I can view team FRT and resolution time
- As a Supervisor, I can export team reports
- As a Supervisor, I can set up alerts for queue backlog

**Acceptance Criteria**:
- [ ] Team dashboard loads in < 2 seconds
- [ ] Alerts sent within 1 minute of threshold breach
- [ ] Reports accurate to within 5 minutes

---

### Team Lead

**Team Management**:
- As a TL, I can view all conversations in my team
- As a TL, I can assign conversations to agents in my team
- As a TL, I can handle escalations
- As a TL, I can view team metrics

**Quality Assurance**:
- As a TL, I can review closed conversations
- As a TL, I can add feedback notes for agents
- As a TL, I can identify training opportunities

**Acceptance Criteria**:
- [ ] Can assign conversations in < 3 clicks
- [ ] Escalations flagged in real-time
- [ ] Feedback notes visible to agents

---

### Agent

**Inbox Management**:
- As an Agent, I can see my assigned conversations
- As an Agent, I can take conversations from my team queue
- As an Agent, I can see unread message count
- As an Agent, I can filter conversations by status

**Customer Interaction**:
- As an Agent, I can send messages to customers
- As an Agent, I can see message delivery status
- As an Agent, I can send images/files (future)
- As an Agent, I can use message templates

**Conversation Management**:
- As an Agent, I can add tags to conversations
- As an Agent, I can add internal notes
- As an Agent, I can close conversations with a reason
- As an Agent, I can search conversation history

**Collaboration**:
- As an Agent, I can chat with other agents
- As an Agent, I can ask for help in internal chat
- As an Agent, I can see which agents are online

**AI Assistance**:
- As an Agent, I get suggested replies from AI
- As an Agent, I can use AI to search tickets
- As an Agent, I can use AI to check transaction status
- As an Agent, I can create transactions with AI help

**Acceptance Criteria**:
- [ ] Inbox loads in < 1 second
- [ ] Message send in < 500ms
- [ ] AI suggestions appear in < 2 seconds
- [ ] Can take from queue in 1 click

---

## Technical Debt & Improvements

### Performance
- [ ] Implement database read replicas
- [ ] Add CDN for media files
- [ ] Optimize slow queries (> 1s)
- [ ] Implement pagination for large lists

### Security
- [ ] Add 2FA for admin accounts
- [ ] Implement API rate limiting
- [ ] Add CSRF protection
- [ ] Regular security audits

### Reliability
- [ ] Add database backups (daily)
- [ ] Implement disaster recovery plan
- [ ] Add health checks for all services
- [ ] Set up monitoring and alerting

### Developer Experience
- [ ] Add API documentation (Swagger)
- [ ] Create developer onboarding guide
- [ ] Add integration tests
- [ ] Set up CI/CD pipeline

---

## Success Metrics

### MVP 1
- [ ] 200 agents onboarded
- [ ] 300+ messages/day handled
- [ ] < 5% error rate
- [ ] 99% uptime

### MVP 2
- [ ] 80% conversations auto-routed correctly
- [ ] FRT < 5 minutes (p95)
- [ ] Resolution time < 30 minutes (p95)
- [ ] Agent satisfaction > 4/5

### MVP 3
- [ ] 50+ AI tool calls/day
- [ ] 0 unauthorized tool calls
- [ ] Integration uptime > 99.5%
- [ ] Customer satisfaction > 4/5 (future)

---

**End of Documentation**

For questions or clarifications, contact the architecture team.
