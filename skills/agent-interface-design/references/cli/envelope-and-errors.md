# JSON Envelope and Error Contract

> Read when: you are specifying or auditing the JSON a CLI prints in `--json` mode, success or failure.

<!-- src: audit-agentic-cli/references/output-contracts.md#Output Contracts Reference -->
## Purpose

These contracts let an agent parse every response, handle errors and orchestrate workflows without guessing. This directory is the canonical home for JSON envelopes, structured errors, stdout/stderr separation, stream formats and the exit-code taxonomy. Exit codes: `exit-codes.md`. Error classes: `error-classes.md`. Formal schemas: `envelope-schemas.md`.

<!-- src: audit-agentic-cli/references/output-contracts.md#1. Structured Output Standards | audit-agentic-cli/references/output-contracts.md#JSON Output Requirements -->
## JSON output requirements

Every agent-friendly CLI supports structured JSON output.

| Requirement | Implementation |
|-------------|----------------|
| Flag | `--json` or `--output json` |
| stdout | Data ONLY: no logs, no progress, no warnings |
| stderr | Logs, progress indicators, warnings, debug info |
| Structure | Prefer flat over deeply nested |
| Types | Consistent: numbers stay numbers, dates as ISO 8601 |

> Reconciled: the sources put error JSON on stdout in one file and stderr in another; this file uses one rule. In `--json` mode the envelope (success and failure) is written once to stdout; stderr carries human diagnostics only and never JSON. A CLI that varies by case, or that documents neither, is the finding.

<!-- src: audit-agentic-cli/references/output-contracts.md#Success Envelope -->
## Success envelope

```json
{
  "ok": true,
  "command": "deploy apply",
  "schema_version": "1.0",
  "result": {
    "id": "deploy_123",
    "status": "succeeded",
    "resources_created": 3
  },
  "meta": {
    "truncated": false,
    "total_count": 3,
    "duration_ms": 1234
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `ok` | boolean | Always `true` for success |
| `command` | string | The command that was executed |
| `schema_version` | string | Output schema version for forward compatibility |
| `result` | object | The actual operation result |
| `meta` | object | Metadata about the response. `meta.total_count` is the number of items available for a list operation; a paginated list carries the same figure as `result.total` (`pagination.md`): emit one of the two, `result.total`, not both |

<!-- src: audit-agentic-cli/references/output-contracts.md#Error Envelope -->
## Error envelope

```json
{
  "ok": false,
  "error": {
    "class": "conflict",
    "code": "RESOURCE_EXISTS",
    "message": "Resource 'foo' already exists",
    "retryable": false,
    "suggestion": "Use --force to overwrite or choose a different name",
    "details": {
      "existing_id": "res_abc123",
      "created_at": "2024-01-15T10:00:00Z"
    }
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `ok` | boolean | Always `false` for errors |
| `error.class` | string | Error category (see `error-classes.md`) |
| `error.code` | string | Machine-readable error code |
| `error.message` | string | Human-readable description |
| `error.retryable` | boolean | Whether the operation can be retried |
| `error.suggestion` | string | Actionable fix suggestion |
| `error.details` | object | Additional context-specific information |

Stdout is the data channel, stderr the operator channel, the exit code the semantic class. All three must agree (see `exit-codes.md`). The smallest viable envelope and the build order for repairing a CLI are in `repair-build-order.md`.
