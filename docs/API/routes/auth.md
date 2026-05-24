# Route Module: `auth.ts`

Base path: `/api/auth`

## Responsibilities
- User registration
- User login/logout
- Token refresh/session lifecycle
- Auth context bootstrap

## Security
- Login rate limiter enabled
- Password validation and hashing
- Email domain policy checks (allow/block and disposable domains)
- Session hashing and token verification

## Key Notes
- Username collision handling includes suggestion generation.
- Refresh token state is persisted in DB-backed user sessions.

