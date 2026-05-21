## Agent Report

task_id: T006
agent: agent-3
file: backend
status: DONE

### FOUND
Read-only backend/security review found permissive CORS with credentials, hardcoded JWT fallback, unused loginLimiter, unauthenticated item mutations, missing admin checks for lesson mutations, repeatable XP rewards, insecure Traefik dashboard defaults, HTTP-only compose routers, and weak DB fallback risks.

### FIXED
GPT verified and fixed CORS allowlist behavior, production JWT secret fail-fast, login/register limiter usage, admin-only item and lesson mutations, idempotent lesson/quiz XP, and production DB credential fail-fast in code.

### CHANGED_FILES
- backend/server.ts
- backend/api/middleware/auth.ts
- backend/api/middleware/errorHandler.ts
- backend/api/routes/auth.ts
- backend/api/routes/items.ts
- backend/api/routes/lessons.ts
- backend/api/routes/quizzes.ts
- backend/api/data/db.ts

### COMMANDS_RUN
- subagent read-only scan
- backend build/lint rerun by GPT after fixes

### RESULT
Report accepted after manual verification; code-level security fixes applied where directly testable.

### RISKS
Compose Traefik TLS/dashboard hardening remains environment-sensitive and should be handled with deployment-specific domain/certificate settings.

### NEXT
Add integration tests for admin-only mutations and idempotent XP once a test database is available.
