# Architecture

## System Context

Hebrew AI Platform is a multi-service learning platform composed of:
- `frontend-react`: web UI for learners and administrators
- `backend`: API, authentication, RBAC, auditing, telemetry
- `ai_bridge`: Python orchestration runtime for agent workflows
- `infra`: routing, logging, and observability services

## High-Level Component Map

1. Client Layer
- Browser clients consume REST API endpoints.
- User and admin UX is rendered by React/Vite frontend.

2. Application Layer
- Express backend handles auth/session lifecycle, domain policies, RBAC checks, and content operations.
- Admin scope is isolated under `/api/admin/*` with stricter role and permission gates.

3. AI Orchestration Layer
- `ai_bridge` decomposes root tasks into DAG-like atomic tasks.
- Routing is capability-driven; model selection is risk/complexity-aware.
- Quality gates, feedback loops, and result merging drive final output quality.
- For current model/provider routing, see [AI Bridge Runtime Routing](./AI_BRIDGE_RUNTIME_ROUTING.md).
- For deeper technical background, see [AI Orchestrator: Core Technical Reference](./AI_ORCHESTRATOR_CORE.md).

4. Data and State Layer
- PostgreSQL: primary persistence and relational constraints.
- Redis: cache/session acceleration.
- SQL migrations under `backend/database/migrations/` are the source of schema truth.

5. Edge and Observability Layer
- Traefik routes external traffic.
- Loki + Promtail collect logs.
- Grafana provides dashboards and operational visibility.

## Core Runtime Flows

### User Authentication Flow
1. User submits credentials or registration form.
2. Backend validates input and domain policies.
3. Backend issues access/refresh tokens and persists session hash.
4. Frontend uses authenticated API calls with role-aware UI access controls.

### Administrative Control Flow
1. Request enters `/api/admin/*`.
2. Middleware chain enforces token validity, rate limit, role requirements.
3. Route-level permission checks enforce action-level RBAC policy.
4. Action and request context are written to telemetry and audit streams.

### AI Orchestration Flow
1. Root task enters orchestrator.
2. Task is decomposed into atomic tasks with dependencies.
3. Model selector and scheduler pick route and execution profile.
4. Agent executes task; quality analyzer verifies output.
5. Feedback loop triggers fix tasks if quality thresholds are not met.
6. Result merger combines outputs into final response.

## Cross-Cutting Concerns

### Security
- Strict RBAC separation between regular and administrative surfaces.
- Session/token protection and security middleware.
- Email domain allow/block policies for registration hardening.

### Auditability
- Structured audit trails for administrative actions.
- Request-level telemetry for diagnosis and traceability.

### Reliability
- Health checks for app and infra services.
- Container-level restart policies.
- CI checks for docs/API consistency.

## Source of Truth

- API runtime behavior: `backend/api/routes/*`, `backend/api/middleware/*`
- RBAC rules: `backend/api/security/*`, migrations `005+`
- DB schema history: `backend/database/migrations/*`
- AI runtime behavior: `ai_bridge/core/*`, `ai_bridge/agents/*`
- Infrastructure routing/logging: `docker-compose.yml`, `infra/*`

