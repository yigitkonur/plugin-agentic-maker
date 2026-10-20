# Batch Size, Concurrency and Failure Thresholds

> Read when: you are setting the flags and the report that bound a large batch run.

<!-- src: audit-agentic-cli/references/execution-patterns.md#10. Batch Operation Limits | audit-agentic-cli/references/execution-patterns.md#Batch Size and Concurrency Controls -->
## Controls

```bash
mycli bulk-create \
  --input items.json \
  --batch-size 100 \
  --max-concurrent 5 \
  --delay-between-batches 1s \
  --max-items 10000 \
  --continue-on-error \
  --fail-threshold 0.1                 # Stop if >10% failures
```

<!-- src: audit-agentic-cli/references/execution-patterns.md#Batch Flag Standards -->
## Flag standards

| Flag | Description | Default |
|------|-------------|---------|
| `--batch-size <n>` | Items per batch | 100 |
| `--max-concurrent <n>` | Parallel workers | 5 |
| `--delay-between-batches <duration>` | Pause between batches | 0 |
| `--max-items <n>` | Maximum items to process | unlimited |
| `--continue-on-error` | Continue on item failures | false for destructive batches, true otherwise |
| `--stop-on-error` | Stop on first failure | true for destructive batches, false otherwise |
| `--fail-threshold <ratio>` | Stop if failure ratio exceeds | 1.0 |
| `--dry-run` | Preview without executing | false |
| `--retry-failed <n>` | Retry failed items n times | 0 |

<!-- src: audit-agentic-cli/references/execution-patterns.md#Partial Failure Response -->
## Full partial-failure report

Exit 8. Same shape as `batch-and-partial.md`, with counts, timing, batch accounting and per-item location.

```json
{
  "ok": false,
  "status": "partial_failure",
  "exit_code": 8,
  "summary": {
    "total_input": 1000, "processed": 1000, "succeeded": 950,
    "failed": 50, "skipped": 0, "failure_rate": 0.05
  },
  "timing": {
    "started_at": "2024-01-15T10:30:00Z",
    "completed_at": "2024-01-15T10:35:30Z",
    "elapsed": "5m30s",
    "items_per_second": 3.03
  },
  "batches": { "total": 10, "completed": 10, "batch_size": 100, "max_concurrent": 5 },
  "succeeded": [
    {"id": "item-1", "result": {"resource_id": "res_abc123"}}
  ],
  "failed": [
    {
      "id": "item-51",
      "batch_index": 0,
      "item_index": 50,
      "attempts": 3,
      "error": { "class": "validation", "code": "INVALID_INPUT", "message": "Field 'email' is invalid" }
    }
  ],
  "recovery": {
    "failed_items_file": "./failed-items-2024-01-15T10-35-30.json",
    "retry_command": "mycli bulk-create --input ./failed-items-2024-01-15T10-35-30.json"
  }
}
```

Implementations: `../frameworks/go/execution-patterns-batch.md`, `../frameworks/python/execution-patterns-batch.md`.
