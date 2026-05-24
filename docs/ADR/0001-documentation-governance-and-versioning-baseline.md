# ADR-0001: Documentation Governance and Versioning Baseline

Date: 2026-05-24  
Status: Accepted

## Context

The codebase evolved quickly across backend, frontend, AI orchestration, and infrastructure.  
Documentation existed but was fragmented, and versioning practices were not consistently enforced across API, migrations, and releases.

## Decision

Adopt a repository-wide documentation governance baseline with:
- standardized docs structure (`ARCHITECTURE`, `API`, `ADR`, `RUNBOOKS`)
- release and semantic versioning policy
- changelog discipline
- migration playbook
- RBAC/security traceability artifacts
- CI checks for local markdown links and API route-doc coverage

## Alternatives Considered

- Keep existing ad-hoc docs and rely on reviewer discipline only.
- Introduce governance only for backend and defer frontend/infra.
- Use external documentation tooling before fixing internal structure.

## Consequences

### Positive
- Better onboarding and incident response quality.
- Deterministic change traceability from code to docs.
- Lower risk of undocumented API drift.

### Negative
- Additional documentation work in each PR.
- CI may fail for incomplete docs during transition.

## Rollback / Exit Strategy

If process overhead becomes too high, keep mandatory checks only for:
- API route documentation coverage
- changelog updates for release branches

Other governance checks can remain policy-only without CI enforcement.

## References

- `docs/VERSIONING_POLICY.md`
- `docs/DB_MIGRATION_PLAYBOOK.md`
- `docs/API/README.md`
- `CHANGELOG.md`

