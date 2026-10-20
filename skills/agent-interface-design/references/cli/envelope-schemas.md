# Envelope JSON Schemas

> Read when: you need the formal Draft-07 schema for the success or error envelope so an integration can validate CLI output.

<!-- src: audit-agentic-cli/references/output-contracts.md#2. JSON Schema Definitions (Draft-07) -->
## Why schemas

Formal schemas enable compile-time validation and IDE support for agent integrations. A validation example for a Node integration is in `../frameworks/node/output-contracts.md`. The pagination schema is in `pagination.md`; the JSONL event schema is in `jsonl-event-schema.md`.

> Unresolved: the sources disagree on `schema_version` (the minimal envelope uses `"v1"`, the full envelope and schema use `"1.0"` matching `^\d+\.\d+$`), and on whether a failure carries `"result": null, "error": null` fields (minimal) or omits them (full). Pick one form per CLI and document it. Also, both schemas below set top-level `additionalProperties: false`, yet other examples add top-level fields (`dry_run`, `changes`, `status`, `partial_result`, `recovery`, `retry`, `guidance`); widen the top level or nest those fields in `result`/`meta`.

<!-- src: audit-agentic-cli/references/output-contracts.md#Success Response Schema -->
## Success response schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://schemas.cli-agents.dev/success-response.json",
  "title": "SuccessResponse",
  "description": "Standard envelope for successful CLI operations",
  "type": "object",
  "required": ["ok", "result"],
  "properties": {
    "ok": { "type": "boolean", "const": true, "description": "Always true for success responses" },
    "command": {
      "type": "string",
      "description": "The command that was executed",
      "examples": ["deploy apply", "resource create", "config set"]
    },
    "schema_version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+$",
      "description": "Semantic version of the output schema",
      "default": "1.0"
    },
    "result": { "description": "The operation result payload (type varies by command)" },
    "meta": {
      "type": "object",
      "description": "Response metadata",
      "properties": {
        "truncated": { "type": "boolean", "description": "Whether the result was truncated", "default": false },
        "total_count": { "type": "integer", "minimum": 0, "description": "Total items available (for list operations)" },
        "duration_ms": { "type": "integer", "minimum": 0, "description": "Operation duration in milliseconds" },
        "request_id": { "type": "string", "description": "Unique request identifier for debugging" }
      },
      "additionalProperties": true
    }
  },
  "additionalProperties": false
}
```

<!-- src: audit-agentic-cli/references/output-contracts.md#Error Response Schema -->
## Error response schema

The `class` enum below is the reconciled list from `error-classes.md` (it adds `usage` to the source enum).

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://schemas.cli-agents.dev/error-response.json",
  "title": "ErrorResponse",
  "description": "Standard envelope for failed CLI operations",
  "type": "object",
  "required": ["ok", "error"],
  "properties": {
    "ok": { "type": "boolean", "const": false, "description": "Always false for error responses" },
    "error": {
      "type": "object",
      "required": ["class", "code", "message"],
      "properties": {
        "class": {
          "type": "string",
          "enum": ["usage", "not_found", "conflict", "validation", "auth", "rate_limit",
                   "timeout", "network", "internal", "dependency_failed", "partial_success"],
          "description": "Error category for semantic handling"
        },
        "code": {
          "type": "string",
          "pattern": "^[A-Z][A-Z0-9_]*$",
          "description": "Machine-readable error code (SCREAMING_SNAKE_CASE)",
          "examples": ["RESOURCE_EXISTS", "TOKEN_EXPIRED", "RATE_EXCEEDED"]
        },
        "message": { "type": "string", "minLength": 1, "description": "Human-readable error description" },
        "retryable": { "type": "boolean", "description": "Whether the operation can be retried", "default": false },
        "suggestion": { "type": "string", "description": "Actionable guidance for resolution" },
        "retry_after": { "type": "integer", "minimum": 0, "description": "Seconds to wait before retrying (for rate_limit)" },
        "details": { "type": "object", "description": "Additional context-specific information", "additionalProperties": true },
        "failed_operations": {
          "type": "array",
          "description": "List of failed items (for partial_success)",
          "items": {
            "type": "object",
            "required": ["id", "error"],
            "properties": { "id": { "type": "string" }, "error": { "type": "string" } }
          }
        },
        "succeeded_operations": {
          "type": "array",
          "description": "List of succeeded items (for partial_success)",
          "items": {
            "type": "object",
            "required": ["id"],
            "properties": { "id": { "type": "string" }, "result": {} }
          }
        }
      },
      "additionalProperties": true
    }
  },
  "additionalProperties": false
}
```
