# Versioning Policy

## Semantic Versioning

The repository follows `MAJOR.MINOR.PATCH`.

- `MAJOR`: breaking API/contract changes, incompatible schema or behavior shifts.
- `MINOR`: backward-compatible feature additions.
- `PATCH`: backward-compatible fixes and hardening updates.

## Release Tagging

- Tags must use `vX.Y.Z` format.
- Every release tag must map to:
  - `CHANGELOG.md` entry
  - release manifest (`docs/RELEASE_MANIFEST_TEMPLATE.md`)
  - rollback plan reference

## Component Version Manifest

Each release must include explicit versions for:
- root package version
- backend package version
- frontend package version
- AI bridge commit/compatibility marker
- container image tags/digests

## Compatibility Rules

1. API-breaking backend changes require:
- major version bump
- migration notes
- deprecation/upgrade guidance

2. Non-breaking endpoint additions:
- minor version bump
- route docs update

3. Internal-only fixes:
- patch version bump

## Branching and Promotion

- Development changes must be validated by tests and docs checks.
- Production promotion must reference a release manifest and changelog section.

