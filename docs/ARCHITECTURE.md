# System Architecture

Hebrew AI Platform is a multi-service learning platform composed of a React frontend, a Node.js backend, and a Python-based AI orchestration layer.

## 1. High-Level Component Map

1. **Client Layer**: Browser clients consume REST API endpoints. User and admin UX is rendered by React/Vite frontend (`frontend-react`).
2. **Application Layer**: Express backend (`backend`) handles auth/session lifecycle, domain policies, RBAC checks, and content operations.
3. **AI Orchestration Layer**: `ai_bridge` (Python) decomposes root tasks into atomic agent workflows.
4. **Data Layer**: PostgreSQL for persistence and Redis for cache/sessions.
5. **Observability**: Traefik (edge), Loki/Promtail (logs), Grafana (dashboards).

## 2. AI Bridge & Orchestration

The `ai_bridge` is a modular runtime for autonomous agent workflows.

### 2.1 Core Components
- **Orchestrator**: Handles intake, decomposition, routing, execution, and validation.
- **ModelSelector**: Classifies task complexity (LOW, MEDIUM, HIGH, CRITICAL) and picks models.
- **TaskRouter & SmartScheduler**: Assign tasks to agents based on capability and availability.
- **SecurityGate**: Validates shell commands and redacts secrets before sending data to external AI providers.

### 2.2 Runtime Flow
1. Root task is decomposed into atomic tasks (`PLAN`, `CODE`, `TEST`, `REVIEW`).
2. Model plan is built based on complexity and session token budget.
3. Agents execute tasks in a rootless sandbox for isolation.
4. `QualityAnalyzer` and `FeedbackLoop` verify output and trigger `FIX` tasks if needed.
5. `ResultMerger` assembles the final response.

### 2.3 Model Routing
Routing is provider-agnostic. It prefers live account model lists from OpenAI (if enabled) and falls back to Gemini, Mistral, or local agents.
- **Low**: local or lightweight provider.
- **Medium**: Mistral/Gemini.
- **High/Critical**: Stronger providers (OpenAI GPT-4 series) if budget allows.

## 3. Data and Security

### 3.1 Persistence
SQL migrations under `backend/database/migrations/` are the source of truth for the PostgreSQL schema.

### 3.2 Security and RBAC
- **RBAC**: Strict separation between user and administrative surfaces (`/api/admin/*`).
- **Auth**: JWT-based access/refresh tokens with refresh token hashes stored in `user_sessions`.
- **Policy**: Email domain allow/block lists to harden registration.

## 4. Observability & Maintenance
- **Logging**: Centralized logs via Loki/Promtail.
- **Metrics**: Exported to Prometheus/Grafana.
- **Health**: Standard `/api/health` probes for all services.

## 5. Memory Architecture Vision
The system is evolving toward a persistent cognitive layer:
- **Vector Storage**: Using `pgvector` for long-term memory.
- **Advanced RAG**: Hybrid search (BM25 + Vector) and cross-encoder reranking.
- **Context Optimization**: Adaptive injection to minimize token bloat.
- **Self-Healing**: Autonomous pruning of stale or contradictory memories.

## 6. Test Coverage
- **Backend**: API smoke paths and endpoint behavior checks.
- **AI Bridge**: Orchestrator flows, routing logic, and protocol reassembly.
- **System**: Integration-level assertions and deployment validations.
