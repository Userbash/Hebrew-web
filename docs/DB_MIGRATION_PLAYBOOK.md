# Database Migration Playbook

## Scope

Operational standard for creating, reviewing, deploying, and rolling back SQL migrations.

## Migration Design Rules

1. One logical change per migration file.
2. Use incremental numbering under `backend/database/migrations/`.
3. Include comments describing purpose and impact.
4. Prefer additive migrations first; avoid destructive changes in the same release.

## Pull Request Requirements

Every migration PR must include:
- migration purpose
- affected tables/indexes/constraints
- data backfill requirements
- runtime risk (locks, scan cost)
- rollback strategy

## Deployment Procedure

1. Validate migration in staging dataset.
2. Verify query plans for heavy operations.
3. Apply migration via standard backend startup migration runner.
4. Run smoke checks for affected endpoints.

## Rollback Strategy

If explicit down migration is unavailable:
- execute compensating migration
- restore from backup where required
- disable newly introduced code paths if needed

## Backfill Guidance

- Use batched updates for large datasets.
- Avoid long-running transactions when possible.
- Record completion checkpoint and validation query.

## Post-Deployment Validation

- Check schema state.
- Verify app endpoints touching changed tables.
- Monitor error rates, query latency, and lock metrics.

