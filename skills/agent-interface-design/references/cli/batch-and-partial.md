# Batch Operations and Partial Failure

> Read when: one command processes many items and some may fail while others succeed.

<!-- src: audit-agentic-cli/references/execution-patterns.md#5. Batch Operations | audit-agentic-cli/references/execution-patterns.md#Chunked Processing -->
## Chunked processing

Process in chunks with controlled concurrency.

```bash
mycli bulk-create \
  --input items.json \
  --chunk-size 100 \
  --concurrency 5 \
  --continue-on-error
```

The batch controls (`--batch-size`, `--max-concurrent`, thresholds, delays) are in `batch-limits.md`. A batch is processed chunk by chunk; inside a chunk a semaphore limits concurrent items. The source uses `--chunk-size` / `--concurrency` here and `--batch-size` / `--max-concurrent` in `batch-limits.md`: the same controls; document one set per CLI.

## Stop or continue

> Note: read-only and idempotent batches default to continue and report partial (exit 8). Destructive batches default to stop at the first error. `--stop-on-error` and `--continue-on-error` override either default.

<!-- src: audit-agentic-cli/references/execution-patterns.md#Partial Failure Handling -->
## Partial failure handling

A batch with mixed results exits 8 (`partial`), never 3, and reports every item.

Response structure for a batch command:

```json
{
  "ok": false,
  "status": "partial_failure",
  "summary": { "total": 100, "succeeded": 95, "failed": 5 },
  "succeeded": [
    {"id": "item-1", "resource_id": "res_abc123"},
    {"id": "item-2", "resource_id": "res_def456"}
  ],
  "failed": [
    {
      "id": "item-96",
      "error": { "class": "validation", "code": "INVALID_NAME", "message": "Name contains invalid characters" }
    },
    {
      "id": "item-97",
      "error": { "class": "conflict", "code": "ALREADY_EXISTS", "message": "Resource already exists" }
    }
  ],
  "failed_items_file": "./bulk-create-failed-2024-01-15T10-30-00.json",
  "retry_command": "mycli bulk-create --input ./bulk-create-failed-2024-01-15T10-30-00.json"
}
```

`status` is one of `success`, `partial_failure`, `failed`:

| Condition | `ok` | `status` | Exit |
|-----------|------|----------|------|
| No failures | `true` | `success` | 0 |
| Some succeeded, some failed | `false` | `partial_failure` | 8 |
| Nothing succeeded | `false` | `failed` | the failure's own class code (6 validation, 3 not_found, ...); 8 is for mixed results only |

Always write the failed items to `failed_items_file` and give a `retry_command` that consumes it, so the agent can retry only what failed.

> Note: use this batch response (`status: partial_failure`, top-level `succeeded`/`failed` arrays) for commands that act on many items; use the error form (`error.class: partial_success`, `succeeded_operations`, `failed_operations`, in `error-classes.md`) only when one operation partly completed and cannot list items. Both exit 8. `ok` answers "did the command do what was asked?": a batch asked for 100 creations and made 95, so `false`. A check whose job is to report problems (this plugin's `probe` and `check` commands) ran as asked, so it sets `ok: true` with `status: partial` and the same exit 8.

Implementations: `../frameworks/go/execution-patterns-batch.md`, `../frameworks/python/execution-patterns-batch.md`.
