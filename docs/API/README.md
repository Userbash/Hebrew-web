# API Documentation

## Purpose

This section defines the backend API contracts used by frontend and administrative clients.

## Structure

- `routes/*.md`: one document per backend route module in `backend/api/routes/`
- `ERRORS.md`: shared error model and status-code conventions
- `VERSIONING.md`: API versioning and compatibility policy

## Contract Rules

1. Any endpoint behavior change requires route-doc update in the same pull request.
2. Any request/response schema change requires examples to be updated.
3. Any new security requirement must be reflected in route-level access notes.
4. Breaking changes must be flagged in `CHANGELOG.md` and release notes.

## Current Route Coverage

- `accessControl.ts` -> `routes/accessControl.md`
- `admin.ts` -> `routes/admin.md`
- `auditEvents.ts` -> `routes/auditEvents.md`
- `auth.ts` -> `routes/auth.md`
- `dictionary.ts` -> `routes/dictionary.md`
- `items.ts` -> `routes/items.md`
- `lessons.ts` -> `routes/lessons.md`
- `logs.ts` -> `routes/logs.md`
- `profileAvatar.ts` -> `routes/profileAvatar.md`
- `progress.ts` -> `routes/progress.md`
- `publications.ts` -> `routes/publications.md`
- `quizzes.ts` -> `routes/quizzes.md`
- `systemMetrics.ts` -> `routes/systemMetrics.md`
- `users.ts` -> `routes/users.md`

