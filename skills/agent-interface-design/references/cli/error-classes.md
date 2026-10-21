# Error Classes

> Read when: you are choosing `error.class` and `error.retryable` for a failure, or checking which exit code a class maps to.

<!-- src: audit-agentic-cli/references/output-contracts.md#4. Error Classes -->
## The class list

Standard classes let an agent reason about failures semantically. The class list is: `usage`, `not_found`, `auth`, `conflict`, `validation`, `rate_limit`, `timeout`, `network`, `internal`, `dependency_failed`, `partial_success`. `transient` is the name of the exit-7 group, not a class. The class is `auth` (never `authentication`).

| Class | Description | Example | Retryable |
|-------|-------------|---------|-----------|
| `usage` | Bad flags, invalid arguments, wrong syntax | Unknown flag, missing positional | No |
| `not_found` | Resource doesn't exist | File, user, project not found | No |
| `conflict` | Already exists or version mismatch | Duplicate name, stale ETag | No |
| `validation` | Input doesn't pass validation | Invalid email, bad format | No |
| `auth` | Authentication/authorization failed | Expired token, no permission | No |
| `rate_limit` | Rate limited by server | Too many requests | Yes (with backoff) |
| `timeout` | Operation timed out | API didn't respond in time | Yes |
| `network` | Network connectivity issue | DNS failure, connection refused | Yes |
| `internal` | Internal error (bug) | Unexpected nil pointer | Maybe |
| `dependency_failed` | Upstream service unavailable | Database down, external API error | Yes |
| `partial_success` | Some operations succeeded, some failed | Batch with mixed results | No (check details) |

> Note: there are eleven classes, including `usage`; `transient` is the name of the exit-7 group, not a class.

<!-- src: audit-agentic-cli/references/output-contracts.md#Error Class Examples -->
## Error class examples

Each example is the whole stdout body in `--json` mode.

### rate_limit

```json
{
  "ok": false,
  "error": {
    "class": "rate_limit",
    "code": "RATE_EXCEEDED",
    "message": "Rate limit exceeded: 100 requests per minute",
    "retryable": true,
    "retry_after": 45,
    "suggestion": "Wait 45 seconds or use --rate-limit 50 to throttle requests",
    "details": {
      "limit": 100,
      "window_seconds": 60,
      "current_count": 102,
      "reset_at": "2024-01-15T10:31:00Z"
    }
  }
}
```

### timeout

```json
{
  "ok": false,
  "error": {
    "class": "timeout",
    "code": "OPERATION_TIMEOUT",
    "message": "Operation timed out after 30 seconds",
    "retryable": true,
    "suggestion": "Retry with --timeout 60 or check service health",
    "details": {
      "timeout_ms": 30000,
      "operation": "api_call",
      "endpoint": "https://api.example.com/deploy",
      "last_status": "in_progress"
    }
  }
}
```

### dependency_failed

```json
{
  "ok": false,
  "error": {
    "class": "dependency_failed",
    "code": "DATABASE_UNAVAILABLE",
    "message": "PostgreSQL connection failed: connection refused",
    "retryable": true,
    "suggestion": "Check database status with 'mycli db status' or retry in 30 seconds",
    "details": {
      "dependency": "postgresql",
      "host": "db.example.com:5432",
      "connection_attempts": 3,
      "last_error": "connection refused"
    }
  }
}
```

### partial_success

Exit code 8, never 3.

```json
{
  "ok": false,
  "error": {
    "class": "partial_success",
    "code": "BATCH_PARTIAL_FAILURE",
    "message": "3 of 5 operations succeeded",
    "retryable": false,
    "suggestion": "Retry failed items with: mycli batch retry --failed-only",
    "details": { "total": 5, "succeeded": 3, "failed": 2 },
    "succeeded_operations": [
      { "id": "res_001", "result": { "status": "created" } },
      { "id": "res_002", "result": { "status": "created" } },
      { "id": "res_003", "result": { "status": "created" } }
    ],
    "failed_operations": [
      { "id": "res_004", "error": "VALIDATION_FAILED", "message": "Invalid format" },
      { "id": "res_005", "error": "CONFLICT", "message": "Already exists" }
    ]
  }
}
```

<!-- src: audit-agentic-cli/references/output-contracts.md#Error Class Quick Reference -->
## Class to exit code and retry

| Class | Exit Code | Retryable | Common Causes |
|-------|-----------|-----------|---------------|
| `usage` | 2 | No | Bad flags, wrong syntax |
| `not_found` | 3 | No | Missing resource, invalid ID |
| `auth` | 4 | No | Expired token, missing permissions |
| `conflict` | 5 | No | Duplicate resource, stale version |
| `validation` | 6 | No | Invalid format, constraint violation |
| `rate_limit` | 7 | Yes | Too many requests |
| `timeout` | 7 | Yes | Operation exceeded time limit |
| `network` | 7 | Yes | Connection failed, DNS error |
| `dependency_failed` | 7 | Yes | Upstream service unavailable |
| `internal` | 1 | Maybe | Bug, unexpected state |
| `partial_success` | 8 | No | Batch with mixed results |

Retry strategy per class is in `retry.md`. A Go mapping function is in `../frameworks/go/output-contracts.md`.
