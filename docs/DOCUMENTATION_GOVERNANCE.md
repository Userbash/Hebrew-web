# Documentation Governance

## Objective

Keep documentation synchronized with implementation and release history.

## Mandatory Updates by Change Type

### API route behavior changes
- Update relevant `docs/API/routes/*.md`
- Update examples/schemas where relevant
- Update `CHANGELOG.md`

### Security/auth/RBAC changes
- Update `docs/SECURITY_CHANGELOG.md`
- Update `docs/RBAC_MATRIX.md` when permission behavior changes
- Update admin runbooks/checklists when operational steps are affected

### Database schema changes
- Update migration notes in PR
- Validate against `docs/DB_MIGRATION_PLAYBOOK.md`
- Add release manifest migration section

### Architecture-level decisions
- Add or supersede ADR in `docs/ADR/`
- Update `docs/ARCHITECTURE.md` when runtime flow changes

## CI Enforcement

CI validates:
- markdown local links
- API route documentation coverage
- route/doc change coupling

## Review Gate

A pull request is not ready for merge until:
1. required docs are updated,
2. changelog entry is prepared (or explicitly not required),
3. rollback and risk notes are present for operationally significant changes.

