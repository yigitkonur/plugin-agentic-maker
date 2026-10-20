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

> Reconciled: the sources gave `--stop-on-error` as "default: continue" in one table and implied stop-by-default elsewhere. This file states it once. Read-only and idempotent batches default to continue and report partial (exit 8). Destructive batches default to stop at the first error. `--stop-on-error` and `--continue-on-error` override either default.

<!-- src: audit-agentic-cli/references/execution-patterns.md#Partial Failure Handling -->
## Partial failure handling

A batch with mixed results exits 8 (`partial`), never 3, and reports every item.

> Reconciled: one source batch example reported partial failure as exit 3; this file uses 8 everywhere (`exit-codes.md`).

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
| Nothing succeeded | `false` | `failed` | not stated by the sources; document it |

Always write the failed items to `failed_items_file` and give a `retry_command` that consumes it, so the agent can retry only what failed.

> Unresolved: the sources describe partial results two ways: this batch response (`status: partial_failure`, top-level `succeeded`/`failed` arrays) and the error-envelope form with `error.class: partial_success`, `succeeded_operations`, `failed_operations` (`error-classes.md`). Both use exit 8; pick one shape per CLI and document it.

Implementations: `../frameworks/go/execution-patterns-batch.md`, `../frameworks/python/execution-patterns-batch.md`.
