# MAX - Omnichannel Inbox Platform

## Overview

Internal omnichannel inbox platform for managing customer conversations across WhatsApp Cloud API and proprietary chat app.

**Key Stats:**
- Channels: WhatsApp + Chat App
- Volume: 300-500 messages/day
- Agents: ~200
- Teams: Sales, Support, Customer Service
- Roles: Admin, Supervisor, Team Lead, Agent

## Documentation Structure

0. [Executive Summary](./docs/00-executive-summary.md) - What MAX is and is not
1. [Architecture Overview](./docs/01-architecture.md) - System components and design
2. [Data Model](./docs/02-data-model.md) - Database schema and relationships
3. [States & Flows](./docs/03-states-flows.md) - Conversation states and routing logic
4. [RBAC & Permissions](./docs/04-rbac.md) - Role-based access control
5. [API Contract](./docs/05-api-contract.md) - Internal API endpoints
6. [Integration Hub](./docs/06-integration-hub.md) - External system integrations
7. [AI Tool Gateway](./docs/07-ai-gateway.md) - AI agent security layer
8. [Observability](./docs/08-observability.md) - Logging, metrics, tracing
9. [Roadmap](./docs/09-roadmap.md) - Implementation phases
10. [**Enhancements**](./docs/10-enhancements.md) - **Critical improvements and advanced features**

See [docs/README.md](./docs/README.md) for a comprehensive overview.

## Technology Stack

- **Backend:** Python + FastAPI
- **Database:** PostgreSQL
- **Cache/Queue:** Redis
- **Workers:** Celery
- **Realtime:** WebSockets
- **Monitoring:** Structured logging + metrics

## Quick Start

See [Roadmap](./docs/09-roadmap.md) for implementation phases.
