# Changelog

All notable changes to this project are documented in this file.

The format follows Keep a Changelog principles and Semantic Versioning (`MAJOR.MINOR.PATCH`).

## [Unreleased]

### Added
- Documentation governance baseline:
  - architecture map (`docs/ARCHITECTURE.md`)
  - API documentation structure (`docs/API/*`)
  - ADR registry (`docs/ADR/*`)
  - operations runbooks (`docs/RUNBOOKS/*`)
  - versioning policy (`docs/VERSIONING_POLICY.md`)
  - database migration playbook (`docs/DB_MIGRATION_PLAYBOOK.md`)
  - RBAC matrix (`docs/RBAC_MATRIX.md`)
  - security changelog (`docs/SECURITY_CHANGELOG.md`)
  - test coverage map (`docs/TEST_COVERAGE_MAP.md`)
  - release manifest template (`docs/RELEASE_MANIFEST_TEMPLATE.md`)
- CI documentation quality checks:
  - markdown local-link validation
  - API route documentation coverage validation

### Changed
- Expanded root `README.md` with a documentation index and governance workflow.
- Added root npm scripts for docs verification and route-doc synchronization checks.
- Added pull request template with mandatory risk, migration, rollback, and traceability sections.

## [2.0.0] - 2026-05-24

### Added
- Core backend API services and deployment hardening.
- Extended RBAC, audit, telemetry, and security guardrails.
- AI Bridge orchestration protocol updates and routing stabilization.
- Admin panel and observability improvements.

### Fixed
- Registration security edge cases (disposable domains, CORS origin handling).
- Admin telemetry stability and limiter behavior.

