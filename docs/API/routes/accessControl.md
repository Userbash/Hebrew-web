# Route Module: `accessControl.ts`

Base path: `/api/access`

## Responsibilities
- RBAC catalog retrieval
- Role/group management
- User-role assignment lifecycle

## Security
- Route-level permission checks
- Additional role requirement for sensitive modifications

## Key Notes
- System roles are protected from destructive edits.
- Cache invalidation is triggered after role/permission mutations.
