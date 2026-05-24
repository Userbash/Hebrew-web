# Test Coverage Map

## Purpose

Document what is covered by automated tests and where residual risk remains.

## Test Suites

### Root System Suite
- Path: `tests/`
- Entry: `npm test` -> `tests/run-all-tests.js`
- Covers:
  - deployment/system validations
  - compose/infra checks
  - integration-level assertions

### Backend Suite
- Path: `backend/tests/`
- Commands:
  - `node tests/quick-test.js`
  - `node tests/test-api.js`
- Covers:
  - API smoke paths
  - key endpoint behavior

### AI Bridge Suite
- Path: `ai_bridge/tests/`
- Command: `python3 -m pytest ai_bridge/tests`
- Covers:
  - orchestrator flows
  - routing/scheduling logic
  - protocol framing/reassembly
  - metrics/security checks

## Risk Areas to Expand

1. End-to-end admin mutation tests across role assignment flows.
2. Regression tests for migration compatibility and rollback scenarios.
3. Contract tests validating frontend assumptions against backend route payloads.
4. Failure-injection tests for observability and incident diagnostics.

