# Project Governance & Policies

This document outlines the operational and development standards for the Hebrew AI Platform.

## 1. Documentation Governance
Keep documentation synchronized with implementation and release history.

### 1.1 Mandatory Updates
- **API Changes**: Update relevant `docs/API/routes/*.md` and `CHANGELOG.md`.
- **Security/RBAC**: Update `docs/SECURITY_CHANGELOG.md` and the RBAC matrix.
- **DB Schema**: Update migration notes in PR and validate against the playbook.
- **Architecture**: Update `docs/ARCHITECTURE.md` for runtime flow changes.

### 1.2 CI Enforcement
CI validates markdown local links, API route documentation coverage, and route/doc change coupling.

## 2. Versioning Policy
The repository follows Semantic Versioning (`MAJOR.MINOR.PATCH`).
- **MAJOR**: Breaking API/contract changes, incompatible schema or behavior shifts.
- **MINOR**: Backward-compatible feature additions.
- **PATCH**: Backward-compatible fixes and hardening updates.

### 2.1 Release Tagging
Tags use `vX.Y.Z` format and must map to a `CHANGELOG.md` entry and a release manifest.

## 3. Traceability & Releases
Every material change must be traceable through:
`Issue -> Pull Request -> Commit(s) -> Changelog/Release Manifest -> Runbook/Docs Update`

### 3.1 Release Manifest Metadata
- Git tag and commit SHA.
- Backend/Frontend package versions.
- Infrastructure image tags/digests.
- Applied Migration IDs.

## 4. Database Migration Playbook

### 4.1 Design Rules
- One logical change per migration file.
- Use incremental numbering in `backend/database/migrations/`.
- Prefer additive changes; avoid destructive ones in the same release.

### 4.2 Rollback Strategy
If an explicit down migration is unavailable:
- Execute a compensating migration.
- Restore from backup where required.
- Disable newly introduced code paths.

## 5. Environment Versioning
Ensure every environment (dev/staging/prod) can be reconstructed with explicit versions using lockfiles (`package-lock.json`) and explicit container image tags.

## 6. RBAC Matrix (Administrative Roles)

| Role | Intent | Typical Scope |
| --- | --- | --- |
| `root` | Full platform control | All resources |
| `platform_admin` | Operational administration | Admin APIs and platform controls |
| `security_admin` | Security governance | Audit, access, policy review |
| `content_admin` | Content moderation | Publications and content workflow |
| `support` | User support operations | User assistance with limited mutations |
