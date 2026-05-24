# Change Traceability Policy

## Required Chain

Every material change must be traceable through:

`Issue -> Pull Request -> Commit(s) -> Changelog/Release Manifest -> Runbook/Docs Update`

## Pull Request Requirements

A PR must include:
- issue/ticket reference
- scope of change
- risk assessment
- migration and rollback notes (if applicable)
- documentation updates

## Release Requirements

A release is considered complete only when:
- `CHANGELOG.md` is updated
- release manifest is completed
- impacted runbooks/docs are updated
- validation evidence is recorded

