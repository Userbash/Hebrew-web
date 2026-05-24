# API Error Model

## Standard Response Shape

```json
{
  "success": false,
  "message": "Human-readable error description",
  "code": "OPTIONAL_MACHINE_CODE",
  "details": {}
}
```

## Status Code Conventions

- `200 OK`: successful read/update operation.
- `201 Created`: successful creation.
- `204 No Content`: successful action without payload.
- `400 Bad Request`: validation failure.
- `401 Unauthorized`: missing or invalid authentication context.
- `403 Forbidden`: authenticated but insufficient permissions.
- `404 Not Found`: target resource does not exist.
- `409 Conflict`: duplicate or conflicting state.
- `422 Unprocessable Entity`: syntactically valid request with semantic failure.
- `429 Too Many Requests`: rate limiter triggered.
- `500 Internal Server Error`: unhandled server-side error.

## Operational Requirements

- Keep error messages deterministic and stable for clients.
- Do not return sensitive internals in production error payloads.
- Include trace IDs where available for incident diagnostics.

