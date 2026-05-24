# RBAC Matrix

## Purpose

Human-readable matrix of administrative roles, permissions, and expected scope boundaries.

## Core Administrative Roles

| Role | Intent | Typical Scope |
| --- | --- | --- |
| `root` | Full platform control | All resources |
| `platform_admin` | Operational administration | Admin APIs and platform controls |
| `security_admin` | Security governance | Audit, access, policy review |
| `content_admin` | Content moderation | Publications and content workflow |
| `support` | User support operations | User assistance with limited mutations |

## Permission Domains

- `rbac`: role and permission administration
- `users`: user directory and account lifecycle
- `publications`: content lifecycle moderation
- `audit`: audit trail visibility
- `system`: system metrics and operational health

## Guardrail Principles

1. Least privilege by default.
2. System roles are protected from casual mutation.
3. Sensitive role changes require explicit audit context.
4. Admin endpoints require both role gate and permission gate.

## Change Management

Any RBAC catalog or behavior change must update:
- `backend/api/security/rbacCatalog.ts` / related service logic
- this matrix
- `CHANGELOG.md`
- `docs/SECURITY_CHANGELOG.md` (if security posture changes)

