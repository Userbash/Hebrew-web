# API Reference Guide

This document defines the backend API contracts used by frontend and administrative clients.

## 1. Standard Response Shape

```json
{
  "success": false,
  "message": "Human-readable description",
  "code": "OPTIONAL_MACHINE_CODE",
  "details": {}
}
```

## 2. Status Code Conventions

- **200 OK**: Success.
- **201 Created**: Successful creation.
- **400 Bad Request**: Validation failure.
- **401 Unauthorized**: Missing/invalid authentication.
- **403 Forbidden**: Insufficient permissions.
- **404 Not Found**: Resource does not exist.
- **409 Conflict**: Duplicate or conflicting state.
- **500 Internal Server Error**: Unhandled server error.

## 3. Versioning Policy

The backend exposes non-prefixed routes under `/api/*`.
- **Backward-compatible changes** (new fields/endpoints) are allowed in minor releases.
- **Breaking changes** (removing fields, renaming) require a major version bump or a versioned path (e.g., `/api/v2/*`).

## 4. Documentation Rules

- Any endpoint behavior change requires a route-doc update in `docs/API/routes/*.md`.
- Any schema change requires example updates.
- Breaking changes must be flagged in `CHANGELOG.md`.

## 5. Route Modules

See `docs/API/routes/` for detailed documentation on:
- `auth.ts`: Registration, login, session lifecycle.
- `users.ts`: Profile and account management.
- `admin.ts`: Administrative API composition and gates.
- `accessControl.ts`: RBAC management.
- `publications.ts`: Content moderation and state.
- `systemMetrics.ts`: Health and runtime telemetry.
