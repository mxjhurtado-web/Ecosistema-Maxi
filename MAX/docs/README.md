# MAX Platform - Architecture Documentation Summary

## 📋 Documentation Overview

This folder contains the complete architectural design for **MAX**, an internal omnichannel inbox platform for managing customer conversations across WhatsApp Cloud API and a proprietary chat application.

---

## 📚 Document Index

| Document | Description | Key Topics |
|----------|-------------|------------|
| [00-executive-summary.md](./00-executive-summary.md) | What MAX is and is not | Core capabilities, design principles, success metrics |
| [01-architecture.md](./01-architecture.md) | System components and design | Component diagrams, data flows, technology decisions |
| [02-data-model.md](./02-data-model.md) | Database schema | All tables, fields, indexes, relationships |
| [03-states-flows.md](./03-states-flows.md) | Conversation lifecycle | State machine, triage flow, assignment logic |
| [04-rbac.md](./04-rbac.md) | Role-based access control | Permission matrix, scoping rules, authorization |
| [05-api-contract.md](./05-api-contract.md) | Internal API endpoints | REST API, WebSocket events, request/response examples |
| [06-integration-hub.md](./06-integration-hub.md) | External system integrations | Adapters for ticketing, transactions, error handling |
| [07-ai-gateway.md](./07-ai-gateway.md) | AI security layer | Tool definitions, permissions, confirmation flow |
| [08-observability.md](./08-observability.md) | Logging and monitoring | Metrics, tracing, dashboards, alerting |
| [09-roadmap.md](./09-roadmap.md) | Implementation phases | 3 MVPs, user stories, acceptance criteria |
| [**10-enhancements.md**](./10-enhancements.md) | **Critical improvements** | **Media handling, SLA, canned responses, business hours** |

---

## 🎯 Quick Reference

### System Stats
- **Channels**: WhatsApp Cloud API + Chat App
- **Volume**: 300-500 messages/day
- **Users**: ~200 agents across 3 teams
- **Teams**: Sales, Support, Customer Service
- **Roles**: Admin, Supervisor, Team Lead, Agent

### Technology Stack
- **Backend**: Python + FastAPI
- **Database**: PostgreSQL
- **Cache/Queue**: Redis
- **Workers**: Celery
- **Realtime**: WebSockets

### Key Features
1. **Unified Inbox**: All channels in one interface
2. **Intelligent Routing**: AI-powered triage flow
3. **Queue Management**: Manual + future auto-assignment
4. **Enterprise Integrations**: Ticketing, transactions
5. **AI-Ready**: Copilot and autonomous agents
6. **Internal Chat**: Agent-to-agent collaboration
7. **Complete Audit**: Full event logging and metrics

---

## 🚀 Implementation Roadmap

### MVP 1: Core Inbox (4-6 weeks)
- Basic inbox with manual assignment
- WhatsApp + Chat App support
- Real-time updates via WebSocket
- Role-based access control

### MVP 2: Triage & Routing (3-4 weeks)
- Automated triage flow
- Tags and notes
- Metrics and reporting
- Internal agent chat

### MVP 3: Integrations & AI (4-6 weeks)
- External system integrations
- AI Tool Gateway with security
- AI copilot for agents
- Advanced features (transfer, search)

---

## 🔒 Security Highlights

- **AI Security**: AI never accesses secrets directly; all calls go through secure gateway
- **Audit Trail**: Every action, message, and state change logged
- **RBAC**: Strict role-based permissions with team scoping
- **PII Redaction**: Sensitive data removed from logs
- **Confirmation Flow**: Two-phase commit for financial transactions

---

## 📊 Key Metrics

### Operational
- **FRT (First Response Time)**: Target < 5 min (p95)
- **Resolution Time**: Target < 30 min (p95)
- **Queue Backlog**: Real-time tracking per team
- **Agent Utilization**: Active conversations per agent

### Technical
- **API Latency**: Target < 500ms (p95)
- **Uptime**: Target 99%+
- **Error Rate**: Target < 5%

---

## 🎨 Architecture Highlights

### Component Layers
```
External Channels (WhatsApp, Chat App)
    ↓
Ingress Layer (Webhook validation, normalization)
    ↓
Core API (Business logic, state management)
    ↓
Workers (Triage, metrics, cleanup)
    ↓
Integration Hub (External APIs)
    ↓
AI Tool Gateway (Security layer)
```

### Data Model
- **Core**: users, teams, customers, conversations, messages
- **Audit**: conversation_events, ai_tool_audit_logs
- **Internal**: internal_threads, internal_messages
- **Integrations**: integration_configs, integration_logs

---

## 📖 How to Use This Documentation

### For Developers
1. Start with [Architecture Overview](./01-architecture.md) to understand system design
2. Review [Data Model](./02-data-model.md) for database schema
3. Check [API Contract](./05-api-contract.md) for endpoint specifications
4. See [Roadmap](./09-roadmap.md) for implementation priorities

### For Product Managers
1. Read [Executive Summary](./00-executive-summary.md) for high-level overview
2. Review [States & Flows](./03-states-flows.md) for user journeys
3. Check [Roadmap](./09-roadmap.md) for user stories and acceptance criteria

### For Security/Compliance
1. Review [RBAC](./04-rbac.md) for permission model
2. Check [AI Gateway](./07-ai-gateway.md) for security controls
3. See [Observability](./08-observability.md) for audit logging

---

## 🤝 Next Steps

1. **Review**: Stakeholders review all documentation
2. **Feedback**: Gather feedback and iterate on design
3. **Approval**: Get sign-off from technical and business leads
4. **Planning**: Break down MVP 1 into sprint-sized tasks
5. **Development**: Begin implementation

---

## 📞 Contact

For questions or clarifications about this architecture, contact the architecture team.

**Last Updated**: 2026-01-05
