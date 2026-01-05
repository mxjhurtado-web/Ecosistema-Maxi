# A. Executive Summary

## What MAX Is

**MAX** is an **internal omnichannel inbox platform** designed to unify customer conversations from multiple channels into a single interface for agent teams.

### Core Capabilities

1. **Unified Inbox**: Consolidates WhatsApp Cloud API and proprietary chat app conversations
2. **Intelligent Routing**: Triage flow directs conversations to Sales, Support, or Customer Service teams
3. **Queue Management**: Team-based queues with manual assignment and "take from queue" functionality
4. **Enterprise Integrations**: Secure API connections to ticketing, transaction status, and sales systems
5. **AI-Ready Architecture**: Prepared for AI copilot and autonomous agents with security guardrails
6. **Internal Collaboration**: Agent-to-agent chat separate from customer conversations
7. **Complete Auditability**: Full event logging and operational metrics (FRT, resolution time, backlog)

### Scale & Users

- **Volume**: 300-500 messages/day
- **Agents**: ~200 users across 3 teams
- **Roles**: Admin, Supervisor, Team Lead, Agent
- **Channels**: 2 (WhatsApp + Chat App)

## What MAX Is NOT

- ❌ **Not a SaaS product**: Internal use only, no multi-tenancy
- ❌ **Not a marketing automation tool**: No campaigns, broadcasts, or bulk messaging
- ❌ **Not a CRM**: Integrates with existing systems, doesn't replace them
- ❌ **Not customer-facing**: Agents use this tool; customers use WhatsApp/Chat App
- ❌ **Not a chatbot builder**: AI agents are controlled, not user-configurable flows

## Key Design Principles

1. **Security First**: AI never accesses secrets directly; all integrations go through secure gateways
2. **Audit Everything**: Every action, message, and state change is logged
3. **Human in the Loop**: AI assists but doesn't replace human oversight for critical operations
4. **Scalable Foundation**: Architecture supports future growth (auto-assignment, more channels, more teams)
5. **Operational Excellence**: Built-in metrics, monitoring, and observability from day one

## Success Metrics

- **First Response Time (FRT)**: Time from message arrival to first agent response
- **Resolution Time**: Time from conversation start to closure
- **Queue Backlog**: Number of unassigned conversations per team
- **Agent Utilization**: Active conversations per agent
- **Customer Satisfaction**: Post-conversation ratings (future)

---

**Next**: See [Architecture Overview](./01-architecture.md) for system components.
