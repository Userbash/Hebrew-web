# Full Project Documentation: Hebrew AI Platform

## 1. Project Purpose
Hebrew AI Platform is a web platform for learning and practicing Hebrew with an administrative panel, role and permission management (RBAC), action auditing, telemetry, and a separate AI task orchestration layer (`ai_bridge`).

The project is divided into 4 independent layers:
- `frontend-react` — client application (React + TypeScript + Vite).
- `backend` — API and business logic (Node.js + Express + PostgreSQL + Redis).
- `ai_bridge` — Python orchestrator for multi-agent workflows.
- `infra` + `docker-compose.yml` — container infrastructure, routing, and observability.

## 2. Technology Stack
- Frontend: React, TypeScript, React Router, Bootstrap, Lucide Icons.
- Backend: Express, TypeScript, PostgreSQL, Redis, JWT, bcrypt, helmet, cors, rate limiting.
- AI Bridge: Python 3, pytest, custom protocols and agent routing.
- Infra: Docker/Podman, Traefik, Nginx, Loki, Promtail, Grafana.

## 3. Repository Structure
- `backend/` — server, API routes, middleware, RBAC, DB migrations.
- `frontend-react/` — pages, auth/language/theme contexts, admin panel.
- `ai_bridge/` — task orchestrator, agents, model selector, tests, schemas.
- `infra/` — Loki/Promtail/Grafana configs and edge configs.
- `scripts/` — startup, deployment, bridge integration, and environment automation.
- `docs/` — architecture and operations documentation.

## 4. Architecture and Flows
### 4.1 User flow
1. A user signs up/logs in on the frontend.
2. The backend validates data, creates a session, and sets access/refresh cookies.
3. The frontend works through the API client with role/permission checks.

### 4.2 Administrative flow
1. Access to `/api/admin/*` is allowed only after `verifyToken` + `adminApiLimiter` + `requireRole(['root','platform_admin'])`.
2. All admin operations are validated by RBAC checks (`requirePermission`).
3. Role/permission/user changes are logged to audit and technical logs.

### 4.3 AI flow
1. A root task is decomposed into atomic tasks (`plan/code/test/review`).
2. `ModelSelector` chooses a model/provider and complexity level.
3. `TaskRouter` and `SmartScheduler` route each task to an agent.
4. `FeedbackLoop` and `QualityAnalyzer` verify quality and create fix tasks when needed.
5. `ResultMerger` builds final output and metrics.

## 5. Backend: Implemented Features and Behavior
### 5.1 Entry point
File: `backend/server.ts`
- Uses `helmet`, `cookie-parser`, `compression`, and a global API limiter.
- CORS is configured with origin normalization and wildcard patterns.
- Telemetry and audit middleware are enabled.
- DB migrations and email blocklist auto-update are initialized on startup.
- Routes: `/api/auth`, `/api/users`, `/api/access`, `/api/admin`, `/api/publications`, `/api/profile-avatar`, etc.
- Health endpoint: `/api/health`.

### 5.2 Authentication and sessions
File: `backend/api/routes/auth.ts`
- Registration with email/username normalization.
- Password validation with security rules.
- Disposable email checks plus domain blocklist/allowlist policy.
- Safe username suggestion generation on collisions.
- JWT access/refresh tokens, refresh token hash stored in `user_sessions`.
- Secure comparison via `timingSafeEqual` for critical values.

### 5.3 RBAC and access management
Key files:
- `backend/api/security/rbacCatalog.ts`
- `backend/api/security/rbacService.ts`
- `backend/api/routes/accessControl.ts`
- `backend/api/middleware/authorization.ts`

Implementation:
- Role/permission catalog and hierarchy.
- CRUD for custom roles.
- Role assignment/revocation for users.
- User block/unblock controls.
- Access profile caching with invalidation on updates.

### 5.4 Admin surface
File: `backend/api/routes/admin.ts`
- Strict access hardening for admin API.
- Response cache disabled (`Cache-Control: no-store`).
- Submodules: users, access, publications, metrics, audit, technical logs.

### 5.5 Logging, audit, and security
- `backend/api/middleware/auditTrail.ts` — audit context and critical action logging.
- `backend/api/middleware/telemetry.ts` — request/context telemetry.
- `backend/api/middleware/security.ts` — limiters and abuse protection.
- `backend/api/middleware/errorHandler.ts` — centralized error handling.

### 5.6 Database and migrations
Directory: `backend/database/migrations/`
- `001_init.sql` — base schema.
- `002_user_sessions.sql` — session tables and refresh-token flow.
- `003_users_security_and_search.sql` — user security + search indexes.
- `004_item_metadata_telemetry_and_quiz_attempts.sql` — content and telemetry.
- `005_rbac_roles_permissions.sql` — roles/permissions.
- `006_rbac_strict_admin_hardening.sql` — admin hardening.
- `007_admin_search_indexes.sql` — admin search indexing.
- `008_user_self_service_permissions.sql` — self-service permissions.
- `009_audit_events.sql` — audit events.
- `010_user_telemetry_enhanced_context.sql` — extended telemetry.
- `011_user_ui_preferences.sql` — user UI preferences.

## 6. Frontend: Implemented Features and Behavior
### 6.1 Core logic
- Entry point: `frontend-react/src/main.tsx`.
- Auth/theme/language state via contexts:
  - `context/AuthContext.tsx`
  - `context/ThemeContext.tsx`
  - `context/LanguageContext.tsx`
- API layer:
  - `src/api/client.ts` — base HTTP client.
  - `src/api/admin*.ts`, `src/api/access.ts`, `src/api/publications.ts`.

### 6.2 User interface
- `src/App.tsx` — main dashboard, navigation, status cards, activity blocks.
- `src/components/Layout/*` — sidebar, header, UI preference controls.
- `src/pages/*` — public and user-facing pages.

### 6.3 Admin panel
File: `src/components/Admin/AdminPanel.tsx`
- Main functional sections:
  - Overview/Health
  - User Directory/Create User
  - Groups Catalog/Assignments
  - Publications Moderation
  - Audit Trail/API Logs
- Includes filtering, sorting, CRUD operations, and permission controls.
- Sensitive actions require explicit RBAC checks (`hasPermission`, `canEditUserPermissions`).

## 7. AI Bridge: Implemented Features and Behavior
### 7.1 Core
File: `ai_bridge/core/orchestrator.py`
- Full pipeline wiring: registry, lifecycle, autoscaler, scheduler, router, healthcheck, feedback, KPI, quality, merger.
- `run_task`: model selection, routing, agent execution, quality analysis, auto-fix via feedback loop.
- `run`: DAG execution with dependency handling.

### 7.2 Routing and model selection
- `core/task_router.py` — selects agents by capability.
- `core/model_selector.py` — selects the route by task complexity and risk.
- `core/openai_model_registry.py` — fetches and caches the live OpenAI model list when auto-routing is enabled.
- `core/openai_runtime_router.py` — builds the per-task OpenAI model plan and respects the session token budget.
- `core/provider_budget_router.py` — keeps the task on cheaper Mistral/Gemini/local paths when OpenAI is absent or not worth the cost.
- `core/smart_scheduler.py` — decides P2P vs orchestrator route.

The current runtime does not rely on one fixed OpenAI model name. It prefers
the live account model list, then falls back to the configured provider chain
when OpenAI is not available.

### 7.3 Execution protocol
(commit 2026-05-23)
- `core/message_bus.py` — envelope/transport message model.
- `core/models.py` — task/result/status types.
- `core/result_merger.py` — merges outputs from multiple results.
- `tests/test_protocol.py`, `test_message_bus_envelope.py`, `test_reassemble.py` — framing and reassembly validation.

## 8. Infrastructure and Deployment
### 8.1 Containers
File: `docker-compose.yml`
Services:
- `traefik` — edge/router.
- `postgres`, `redis` — data services.
- `backend`, `frontend` — application services.
- `loki`, `promtail`, `grafana` — observability stack.

### 8.2 Hardening and improvements
- Health checks for backend/frontend/infra services.
- Log rotation (`json-file`, max-size/max-file).
- Service labels for centralized Loki log routing.
- Podman/Docker socket-path support via environment variables.

## 9. Testing
- Backend smoke/API tests: `backend/tests/*`.
- AI bridge unit/integration tests: `ai_bridge/tests/*`.
- System checks: `tests/system/*`.
- Unified runner: `tests/run-all-tests.js`.

## 10. Detailed Change and Fix Log

### 2026-05-24 — `5a75831`
**Topic:** Core backend API implementation and deployment hardening.
**What changed:**
- Full backend scope: data/middleware/routes/security/migrations.
- Strengthened auth, RBAC, audit, telemetry, and CORS policy.
- Updated backend Dockerfile and compose configuration.
- Added pre-push hooks and secret-scan workflow.
**Why:** to close functional gaps and bring backend to a cohesive production-ready state.

### 2026-05-23 — `30fa34c`
**Topic:** AI Bridge orchestration protocol with network-like framing.
**What changed:**
- `message_bus.py`, `models.py`, `result_merger.py`, `smart_scheduler.py`, `task_router.py`.
- Added/updated protocol and reassembly tests.
**Why:** to formalize task/response transport and stabilize multi-step orchestration.

### 2026-05-23 — `a321dc3`
**Topic:** AI Bridge routing consolidation and admin hardening.
**What changed:**
- AI bridge: `model_selector.py`, `task_router.py`, `orchestrator.py`.
- Backend: large security/RBAC/admin/auth/routes/migrations package.
- Frontend admin API and user-permission pages.
**Why:** to align AI routing behavior and reduce risks on the admin surface.

### 2026-05-23 — `b857a4e`
**Topic:** Centralized user preferences and localization modernization.
**What changed:**
- `preferencesStore`, `ThemeContext`, `LanguageContext`, `UiPreferencesControls`.
- Dashboard/admin UI updates.
**Why:** to remove preference-state inconsistencies and enforce a single source of truth for theme/language.

### 2026-05-23 — `6a5f45f`
**Topic:** Unified design system, stronger RBAC, and AI Bridge improvements.
**What changed:**
- Frontend layout/pages/security.
- Backend user/publication access logic.
- AI bridge security/task router and Gemini CLI agent.
**Why:** to align UX and access-control behavior across modules.

### 2026-05-22 — `1eb7326`
**Topic:** Admin panel redesign and infra updates.
**What changed:**
- `AdminPanel.tsx/.css`, admin runbook/checklist/roadmap.
- `docker-compose.admin.yml`, production start/stop scripts.
**Why:** to simplify operations and provide reproducible admin deployment.

### 2026-05-22 — `56ff64d`
**Topic:** User profile and avatar support in admin console.
**What changed:**
- `profileAvatar` route, auth/server/docker/start scripts.
- Admin UI updates for profile block.
**Why:** to add managed profile functionality and avatar storage.

### 2026-05-22 — `fad7a50`
**Topic:** Admin telemetry and rate-limit stabilization.
**What changed:**
- `security.ts`, `telemetry.ts`, `logs.ts`, admin panel.
**Why:** to reduce metric fluctuations and minimize false limiter triggers.

### 2026-05-22 — `a756863`
**Topic:** Major admin update and system-wide audit.
**What changed:**
- Backend audit/access/admin/auth/logs/system routes.
- Migrations `008`, `009`, `010`.
- Frontend admin API clients and screens.
**Why:** to establish full end-to-end auditability of administrative actions.

### 2026-05-22 — `f6cea9b`
**Topic:** Comprehensive security and RBAC hardening.
**What changed:**
- Strengthened `authorization`, `security`, `telemetry`.
- Expanded RBAC services and migrations `004-007`.
- Updated auth/admin frontend components.
**Why:** to enforce access control consistently across API, UI, and DB.

### 2026-05-21 — `f4cb76a`
**Topic:** Registration security and CORS handling.
**What changed:**
- `auth.ts`, `emailDomainBlocklist.ts`, `server.ts`.
- Blocklist update script and env configuration.
**Why:** to reduce fake registrations and fix origin-policy issues.

### 2026-05-21 — `fd059de`
**Topic:** Backend/frontend refactor and auth/DB-layer improvements.
**What changed:**
- Auth middleware, db/redis, migrations `001-003`.
- Dashboard/Auth UI and API schema.
- Updated AI bridge architecture docs.
**Why:** to normalize the baseline architecture and prepare a stable foundation for subsequent hardening.

## 11. What Was Fixed (by Problem Class)
- Access security:
  - strict RBAC checks introduced in admin and access APIs;
  - governance rules for roles and permissions added;
  - admin restrictions enforced at middleware level.
- Registration security:
  - disposable email filtering;
  - domain blocklist/allowlist;
  - username collision handling with valid alternative generation.
- Observability:
  - enhanced telemetry and audit events;
  - centralized logs via Loki/Promtail;
  - service health checks.
- Infrastructure stability:
  - Dockerfile/compose alignment;
  - improved launch scenarios (manual/prod).
- UI consistency:
  - centralized theme/language/preferences;
  - redesigned admin navigation and user dashboard flow.
- AI orchestration:
  - network-like task exchange protocol added;
  - improved agent routing and model selection;
  - stronger feedback loop and quality checks.

## 12. Practical Role of Key Subsystems
- RBAC: prevents unauthorized admin operations.
- Audit Trail: provides traceability of who changed what and when.
- Telemetry: helps detect degradations and incidents through metrics.
- Email Domain Policy: reduces temporary/suspicious account registrations.
- AI Orchestrator: automates multi-step engineering workflows with quality control.
- Observability stack: supports incident investigation through logs and health signals.

## 13. Repository Documents That Complement This Specification
- `README.md` — overall overview and startup instructions.
- `docs/README.md` — central documentation index.
- `docs/AI_BRIDGE_ARCHITECTURE.md` — AI Bridge architecture.
- `docs/RUNBOOKS/OPERATIONS_RUNBOOK.md` — operations runbook.
- `docs/RUNBOOKS/INCIDENT_RESPONSE_RUNBOOK.md` — incident response runbook.
- `infra/loki/README.md` — logging-stack operations.

## 14. Current Repository State
At the time this documentation was prepared, no uncommitted changes were detected (`git status --short` is empty). This document reflects the actual codebase and commit history up to and including `2026-05-24`.
