# Admin Console Split Roadmap

## 1) Цель
Выделить Admin Console в отдельный frontend-сервис без потери общей авторизации, единого backend API и observability.

## 2) Целевая схема
- `app.example.com` -> `frontend-app`
- `admin.example.com` -> `admin-frontend`
- `api.example.com` (или same-origin `/api`) -> `backend`
- Общие сервисы: `postgres`, `redis`, `loki`, `grafana`

## 3) URI контракт (RastAPI)
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `GET /api/admin/health`
- `GET|POST|PATCH /api/admin/users/*`
- `GET|POST|PATCH /api/admin/access/*`
- `GET|POST|PATCH /api/admin/publications/*`
- `GET /api/admin/logs`
- `GET /api/admin/system`
- `GET /api/admin/audit/events`

Принцип: весь admin-функционал только под `/api/admin/*`.

## 4) План исполнения

### Этап 0. Подготовка (1-2 дня)
- Зафиксировать домены: `APP_DOMAIN_NAME`, `ADMIN_DOMAIN_NAME`, `API_DOMAIN_NAME`.
- Зафиксировать cookie policy: `Secure`, `HttpOnly`, `SameSite`, `Domain`.
- Подготовить role matrix по критичным операциям.
- Подготовить threat model (STRIDE-lite).

### Этап 1. Инфраструктурное разделение (2-4 дня)
- Подключить `docker-compose.admin.yml` поверх основного compose.
- Настроить Traefik routers/middlewares отдельно для admin web и admin API.
- Проверить CORS allowlist и preflight для `admin` origin.
- Проверить shared auth flow между app/admin.

### Этап 2. Security hardening (3-5 дней)
- Включить MFA для admin ролей.
- Ввести step-up auth для destructive операций.
- Ужесточить rate limit и anomaly detection для `/api/admin/*`.
- Добавить IP allowlist/VPN/mTLS по возможности.

### Этап 3. Наблюдаемость и контроль (2-3 дня)
- Метрики: latency/error/403/429 для `/api/admin/*`.
- Алерты на suspicious activity.
- Еженедельный отчет по audit events.

### Этап 4. Стабилизация (2-5 дней)
- Pen-test checklist.
- Rollback rehearsal.
- Runbook/SOP по инцидентам.

## 5) Матрица рисков
| Риск | Вероятность | Влияние | Контроль |
|---|---:|---:|---|
| Сессии ломаются между subdomain | M | H | Cookie-domain + e2e login/refresh/logout |
| CORS/CSRF регрессия | M | H | Strict allowlist + CSRF negative tests |
| Non-admin доступ к admin API | L | H | `verifyToken` + `requireRole` + contract tests |
| Ошибка маршрутизации Traefik | M | M | Blue/green + healthcheck + rollback |
| Рост latency | M | M | gzip/keep-alive/cache + tracing |
| Регрессии split-build | M | M | отдельный CI pipeline admin |

## 6) Контрольные точки (Go/No-Go)
- `npm run test` (root) = pass
- `backend build + lint` = pass (warnings only acceptable)
- `frontend build + lint` = pass
- Auth e2e = pass
- Non-admin to `/api/admin/*` = stable 403
- Rollback rehearsal = pass

## 7) Команды запуска (пошагово)
```bash
# 1) Базовый стек
docker compose -f docker-compose.yml up -d

# 2) Наложение admin split
docker compose -f docker-compose.yml -f docker-compose.admin.yml up -d

# 3) Проверка
curl -I http://admin.example.com/
curl -i http://admin.example.com/api/admin/health
```

## 8) Bridge-контроль выполнения
Для безопасного запуска команд в изолированной среде:
```bash
bash scripts/bridge/auto_bridge.sh
bash scripts/bridge/exec.sh docker ps
bash scripts/bridge/exec.sh docker compose -f docker-compose.yml -f docker-compose.admin.yml config
```
