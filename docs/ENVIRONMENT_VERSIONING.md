# Environment Versioning

## Goal

Ensure every environment (dev/staging/prod) can be reconstructed with explicit versions.

## Rules

1. Pin dependency versions via lockfiles:
- root: `package-lock.json`
- backend: `backend/package-lock.json`
- frontend: `frontend-react/package-lock.json`

2. Use explicit container image tags (and digests where possible).

3. For every release, capture:
- compose file revision
- image tags
- runtime env variable snapshot (without secrets)
- migration list

4. Keep environment drift visible:
- compare release manifest against currently deployed stack
- document deviations in deployment notes

## Minimum Release Metadata

- git tag (`vX.Y.Z`)
- commit SHA
- backend/frontend package versions
- infra image versions
- migration IDs applied

