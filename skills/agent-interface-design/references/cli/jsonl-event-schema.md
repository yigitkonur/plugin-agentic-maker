# JSONL Stream Event Schema

> Read when: you need the formal schema for JSONL events a streaming command emits.

<!-- src: audit-agentic-cli/references/output-contracts.md#Stream Event Schema (Draft-07) -->
## Schema

Base schema for streaming JSONL events. Which stream each event type belongs to is in `streams-and-jsonl.md`; the terminal event `completed` may also be named `result` or `summary` (same fields: `status`, `result`, `duration_ms`).

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://schemas.cli-agents.dev/stream-event.json",
  "title": "StreamEvent",
  "description": "Base schema for streaming JSONL events",
  "type": "object",
  "required": ["type"],
  "oneOf": [
    { "$ref": "#/definitions/ProgressEvent" },
    { "$ref": "#/definitions/LogEvent" },
    { "$ref": "#/definitions/CompletedEvent" },
    { "$ref": "#/definitions/ErrorEvent" },
    { "$ref": "#/definitions/HeartbeatEvent" },
    { "$ref": "#/definitions/PhaseEvent" }
  ],
  "definitions": {
    "ProgressEvent": {
      "type": "object",
      "required": ["type", "phase"],
      "properties": {
        "type": { "const": "progress" },
        "phase": { "type": "string", "description": "Current operation phase" },
        "percent": { "type": "integer", "minimum": 0, "maximum": 100 },
        "message": { "type": "string" },
        "timestamp": { "type": "string", "format": "date-time" },
        "eta_seconds": { "type": "integer", "minimum": 0 },
        "items_processed": { "type": "integer", "minimum": 0 },
        "items_total": { "type": "integer", "minimum": 0 }
      }
    },
    "LogEvent": {
      "type": "object",
      "required": ["type", "level", "message"],
      "properties": {
        "type": { "const": "log" },
        "level": { "enum": ["debug", "info", "warn", "error"] },
        "message": { "type": "string" },
        "timestamp": { "type": "string", "format": "date-time" },
        "context": { "type": "object", "additionalProperties": true }
      }
    },
    "CompletedEvent": {
      "type": "object",
      "required": ["type", "status", "result"],
      "properties": {
        "type": { "const": "completed" },
        "status": { "enum": ["succeeded", "failed", "cancelled"] },
        "result": { "description": "Operation result payload" },
        "duration_ms": { "type": "integer", "minimum": 0 }
      }
    },
    "ErrorEvent": {
      "type": "object",
      "required": ["type", "error"],
      "properties": {
        "type": { "const": "error" },
        "error": {
          "type": "object",
          "required": ["class", "code", "message"],
          "properties": {
            "class": { "type": "string" },
            "code": { "type": "string" },
            "message": { "type": "string" },
            "retryable": { "type": "boolean" }
          }
        }
      }
    },
    "HeartbeatEvent": {
      "type": "object",
      "required": ["type"],
      "properties": {
        "type": { "const": "heartbeat" },
        "timestamp": { "type": "string", "format": "date-time" },
        "uptime_ms": { "type": "integer", "minimum": 0 }
      }
    },
    "PhaseEvent": {
      "type": "object",
      "required": ["type", "phase", "status"],
      "properties": {
        "type": { "const": "phase" },
        "phase": { "type": "string" },
        "status": { "enum": ["started", "completed", "skipped", "failed"] },
        "timestamp": { "type": "string", "format": "date-time" },
        "duration_ms": { "type": "integer", "minimum": 0 }
      }
    }
  }
}
```
