# Route Module: `admin.ts`

Base path: `/api/admin`

## Responsibilities
- Administrative API surface composition
- Hard gate for admin-only modules

## Security
- Mandatory token verification
- Admin-only role gate (`root`, `platform_admin`)
- Admin rate limiter
- No-store cache policy for responses

## Mounted Submodules
- users
- access
- publications
- logs
- system
- audit
