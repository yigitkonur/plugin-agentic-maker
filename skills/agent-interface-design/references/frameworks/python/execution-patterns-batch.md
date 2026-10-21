# Python: Bulk Create and Async Batch Processing

> Read when: you are implementing chunked bulk operations, concurrency limits and failure thresholds in a Python CLI.

## Bulk create with partial failure

Contract: `../../cli/batch-and-partial.md`. Exit 8 when `status` is `partial_failure`. Read-only and idempotent batches default to continue; destructive batches default to stop (`continue_on_error=False`).

```python
import asyncio
from dataclasses import dataclass, field
from typing import List, Any

@dataclass
class BulkResult:
    ok: bool
    status: str  # success, partial_failure, failed
    summary: dict
    succeeded: List[dict] = field(default_factory=list)
    failed: List[dict] = field(default_factory=list)

async def bulk_create(
    items: List[dict],
    chunk_size: int = 100,
    concurrency: int = 5,
    continue_on_error: bool = True
) -> BulkResult:
    succeeded = []
    failed = []

    # Process in chunks
    for i in range(0, len(items), chunk_size):
        chunk = items[i:i + chunk_size]

        # Process chunk with semaphore for concurrency control
        semaphore = asyncio.Semaphore(concurrency)

        async def process_item(item):
            async with semaphore:
                try:
                    result = await create_item(item)
                    return ("success", item["id"], result)
                except Exception as e:
                    return ("error", item["id"], classify_error(e))

        results = await asyncio.gather(
            *[process_item(item) for item in chunk],
            return_exceptions=True
        )

        for result in results:
            if result[0] == "success":
                succeeded.append({"id": result[1], **result[2]})
            else:
                failed.append({"id": result[1], "error": result[2]})

        if not continue_on_error and failed:
            break

    # Determine status
    if not failed:
        status = "success"
        ok = True
    elif succeeded:
        status = "partial_failure"
        ok = False
    else:
        status = "failed"
        ok = False

    return BulkResult(
        ok=ok,
        status=status,
        summary={
            "total": len(items),
            "succeeded": len(succeeded),
            "failed": len(failed)
        },
        succeeded=succeeded,
        failed=failed
    )
```

## Batch with limits

Contract: `../../cli/batch-limits.md`.

```python
import asyncio
import sys
import click
from dataclasses import dataclass
from typing import Callable, Optional, TypeVar

T = TypeVar('T')
R = TypeVar('R')

@dataclass
class BatchOptions:
    batch_size: int = 100
    max_concurrent: int = 5
    delay_between_batches: float = 0.0
    max_items: Optional[int] = None
    continue_on_error: bool = True
    fail_threshold: float = 1.0
    retry_failed: int = 0

async def process_batch(
    items: list[T],
    processor: Callable[[T], R],
    options: BatchOptions
) -> dict:
    if options.max_items:
        items = items[:options.max_items]

    semaphore = asyncio.Semaphore(options.max_concurrent)
    succeeded = []
    failed = []

    async def process_with_semaphore(item: T, batch_idx: int, item_idx: int):
        async with semaphore:
            for attempt in range(options.retry_failed + 1):
                try:
                    result = await processor(item)
                    succeeded.append({"id": item["id"], "result": result})
                    return
                except Exception as e:
                    if attempt == options.retry_failed or not is_retryable(e):
                        failed.append({
                            "id": item["id"],
                            "batch_index": batch_idx,
                            "item_index": item_idx,
                            "error": error_to_dict(e)
                        })
                        return
                    await asyncio.sleep(backoff(attempt))

    # Process in batches
    batches = [items[i:i+options.batch_size]
               for i in range(0, len(items), options.batch_size)]

    for batch_idx, batch in enumerate(batches):
        if batch_idx > 0 and options.delay_between_batches > 0:
            await asyncio.sleep(options.delay_between_batches)

        # Check fail threshold
        if len(succeeded) + len(failed) > 0:
            fail_rate = len(failed) / (len(succeeded) + len(failed))
            if fail_rate > options.fail_threshold:
                break

        tasks = [
            process_with_semaphore(item, batch_idx, item_idx)
            for item_idx, item in enumerate(batch)
        ]
        await asyncio.gather(*tasks)

    if not failed:
        status = "success"
    elif succeeded:
        status = "partial_failure"
    else:
        status = "failed"

    return {
        "ok": not failed,
        "status": status,
        "summary": {
            "total": len(items),
            "succeeded": len(succeeded),
            "failed": len(failed)
        },
        "succeeded": succeeded,
        "failed": failed
    }

# CLI
@click.command()
@click.option('--input', 'input_file', required=True)
@click.option('--batch-size', default=100)
@click.option('--max-concurrent', default=5)
@click.option('--delay-between-batches', type=float, default=0.0, help='seconds')
@click.option('--max-items', type=int)
@click.option('--continue-on-error', is_flag=True)
@click.option('--fail-threshold', default=1.0)
@click.option('--retry-failed', default=0)
def bulk_create(input_file, **kwargs):
    items = load_items(input_file)
    options = BatchOptions(**kwargs)

    result = asyncio.run(process_batch(items, create_item, options))
    output_json({"ok": result["ok"], "command": "bulk-create", "schema_version": "1.0",
                 "result": result, "meta": {}})
    # 0 success, 8 partial; all failed: use the failure's own class code (1 here)
    sys.exit({"success": 0, "partial_failure": 8}.get(result["status"], 1))
```
