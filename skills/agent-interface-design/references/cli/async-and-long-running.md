# Async and Long-Running Tasks

> Read when: an operation outlasts a typical agent tool call and needs submit, poll, wait, cancel or streamed progress.

<!-- src: audit-agentic-cli/references/execution-patterns.md#7. Long-Running Task Handling | audit-agentic-cli/references/execution-patterns.md#Submit and Poll Pattern -->
## Submit and poll

Four commands cover the life of a job: submit (returns immediately), status, wait (blocking with a timeout), cancel.

```bash
# Submit (returns immediately)
$ mycli deploy --background
{
  "ok": true,
  "operation_id": "op_abc123",
  "status": "accepted",
  "poll_url": "/operations/op_abc123",
  "poll_interval_ms": 5000
}

# Poll for status
$ mycli task status op_abc123
{
  "operation_id": "op_abc123",
  "status": "running",
  "progress": { "phase": "deploying", "percent": 65, "message": "Deploying to region us-east-1" },
  "started_at": "2024-01-15T10:30:00Z",
  "estimated_completion": "2024-01-15T10:35:00Z"
}

# Wait (blocking with timeout)
$ mycli task wait op_abc123 --timeout 5m
{
  "operation_id": "op_abc123",
  "status": "succeeded",
  "result": { "deployment_id": "dep_xyz789", "url": "https://app.example.com" },
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:34:00Z"
}

# Cancel
$ mycli task cancel op_abc123
{
  "operation_id": "op_abc123",
  "status": "cancelling",
  "message": "Cancellation requested"
}
```

Operation `status` values: `accepted`, `running`, `succeeded`, `failed`, `cancelled` (and `cancelling` while a cancel is pending). `task wait` polls (the reference polls every 2 seconds) and returns the operation when it reaches `succeeded`, `failed` or `cancelled`; on its own timeout it fails with class `timeout` (exit 7). The submit response gives the agent the poll interval (`poll_interval_ms`); it should not poll faster.

<!-- src: audit-agentic-cli/references/execution-patterns.md#Streaming Progress -->
## Streaming progress

When the agent should watch the job rather than poll, `--stream` emits typed events:

```bash
$ mycli deploy --stream
{"type": "started", "operation_id": "op_abc123", "timestamp": "2024-01-15T10:30:00Z"}
{"type": "progress", "phase": "building", "percent": 10, "message": "Installing dependencies"}
{"type": "progress", "phase": "building", "percent": 25, "message": "Compiling application"}
{"type": "progress", "phase": "building", "percent": 50, "message": "Running tests"}
{"type": "progress", "phase": "deploying", "percent": 75, "message": "Uploading artifacts"}
{"type": "progress", "phase": "deploying", "percent": 90, "message": "Starting containers"}
{"type": "completed", "status": "succeeded", "result": {"url": "https://app.example.com"}}
```

> Reconciled: the source printed every event on one stream. Per `streams-and-jsonl.md`, `started` and `progress` lines are progress and go to stderr; the final `completed` line (a result) goes to stdout, so stdout holds exactly one terminal JSON line. The stream loop ends at `completed` or `failed`.

Event types, schema and heartbeat rules: `streams-and-jsonl.md`, `jsonl-event-schema.md`, `jsonl-progress-patterns.md`. Go implementation: `../frameworks/go/execution-patterns-async.md`.
