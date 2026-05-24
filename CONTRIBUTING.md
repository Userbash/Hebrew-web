# Contributing to Hebrew AI Platform

Thank you for contributing. This guide defines the minimum engineering and documentation standards for pull requests.

## 1. Local Setup

```bash
# Root dependencies (test runner + docs checks)
npm install

# Backend dependencies
cd backend && npm install && cd ..

# Frontend dependencies
cd frontend-react && npm install && cd ..

# Environment
cp .env.example .env
```

## 2. Branching

- Create a focused branch per change.
- Prefer branch names such as:
  - `feat/<scope>-<short-description>`
  - `fix/<scope>-<short-description>`
  - `docs/<scope>-<short-description>`

## 3. Commit Standard (Conventional Commits)

Use commit messages in this format:

```text
type(scope): short summary
```

Allowed `type` values:
- `feat`
- `fix`
- `refactor`
- `perf`
- `test`
- `docs`
- `build`
- `ci`
- `chore`

Examples:
- `feat(auth): add refresh token rotation checks`
- `fix(admin): prevent system role deletion`
- `docs(api): add publications route contract`

## 4. Required Validation Before PR

Run these checks locally:

```bash
npm test
npm run docs:check
cd backend && npm run lint && npm run build && cd ..
cd frontend-react && npm run lint && npm run build && cd ..
python3 -m pytest ai_bridge/tests
```

## 5. Documentation Requirements

If your PR changes behavior, update the matching docs in the same PR:
- API changes -> `docs/API/*`
- Architecture/security flow changes -> `docs/ARCHITECTURE.md`, `docs/SECURITY_CHANGELOG.md`
- Migration changes -> `docs/DB_MIGRATION_PLAYBOOK.md` notes and release manifest references
- Any release-significant change -> `CHANGELOG.md`

## 6. Pull Request Requirements

Use `.github/PULL_REQUEST_TEMPLATE.md` and complete all required sections:
- traceability (issue/ADR/docs)
- risk assessment
- migration and rollback notes
- testing evidence

## 7. Versioning and Release

Follow:
- `docs/VERSIONING_POLICY.md`
- `docs/RELEASE_MANIFEST_TEMPLATE.md`
- `CHANGELOG.md`

Any breaking change must be explicitly marked and justified.

## 8. Security Expectations

For changes affecting auth, authorization, secrets, or audit:
- update `docs/SECURITY_CHANGELOG.md`
- update `docs/RBAC_MATRIX.md` if role/permission behavior changes
- include security impact in PR template

