# API Versioning Policy

## Current State

The backend currently exposes non-prefixed routes under `/api/*`.

## Forward Policy

1. Backward-compatible additions are allowed within a minor release:
- new optional request fields
- new response fields
- new endpoints

2. Breaking changes require a versioned path or compatibility layer:
- removing/renaming required fields
- changing semantic meaning of existing fields
- altering auth or permission model in a breaking way

3. Release communication requirements:
- update `CHANGELOG.md`
- include migration notes in release manifest
- document rollback strategy for affected endpoints

## Recommended Evolution Path

- Adopt explicit prefixing for future major versions, e.g. `/api/v2/*`.
- Keep `/api/v1/*` compatibility until announced end-of-support date.

