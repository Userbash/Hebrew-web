# Admin Split Validation Runbook

## 1. Pre-check
```bash
npm run test
cd backend && npm run build && npm run lint
cd ../frontend-react && npm run build && npm run lint
```

## 2. Deploy split
```bash
docker compose -f docker-compose.yml up -d
docker compose -f docker-compose.yml -f docker-compose.admin.yml up -d
```

## 3. Functional validation
1. Login on app -> open admin domain -> session should be valid.
2. `POST /api/auth/refresh` works from admin origin.
3. Non-admin user gets `403` on `/api/admin/*`.
4. Admin user can access `/api/admin/health` and core admin pages.

## 4. Security validation
1. CSRF negative: state-changing request without CSRF token should fail.
2. Rate limit: burst to `/api/admin/*` should return `429`.
3. CORS: disallowed origin should be denied.
4. Headers: HSTS/frame-deny/nosniff present on admin routes.

## 5. Operational validation
1. Healthchecks green for `backend`, `frontend`, `admin-frontend`.
2. Logs contain admin activity with actor and outcome.
3. Alerting catches repeated `401/403/429` spikes.

## 6. Rollback
```bash
# Disable admin split overlay
docker compose -f docker-compose.yml -f docker-compose.admin.yml down admin-frontend

# Ensure base app remains alive
docker compose -f docker-compose.yml up -d
```

## 7. Bug triage map
- Auth/session bug: cookie flags + refresh endpoint + CORS first.
- 403/role bug: RBAC mapping + `requireRole` chain + user role claims.
- Routing bug: Traefik router rule conflicts and priority.
- Performance bug: static cache, compression, backend rate limits.
