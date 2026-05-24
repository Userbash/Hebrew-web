# Route Module: `auditEvents.ts`

Base path: `/api/admin/audit`

## Responsibilities
- Query audit event stream
- Filter by actor/action/resource/outcome

## Security
- Admin-scope access only
- Permission-guarded reads

## Key Notes
- Used for traceability and incident reconstruction.
