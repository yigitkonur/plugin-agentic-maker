# Python: Fetch-All Pagination and Async Rate Limiter

> Read when: you are implementing `--all` cursor pagination or a token-bucket rate limiter with circuit breaker in a Python CLI.

## Fetch all pages

Contract: `../../cli/pagination.md` (`result.items`, `result.next_cursor`, `result.has_more`, optional `result.total`).

> Reconciled: the source's `Page` used `data` / `total_count` and printed `{"ok": True, "data": items, "pagination": {"total_fetched": n}}`. This file uses `items`, `total` and puts the page in `result`.

```python
import click
from typing import Iterator, TypeVar, Generic
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class Page(Generic[T]):
    items: list[T]
    next_cursor: str | None
    total: int | None

def fetch_all_pages(
    fetch_fn: callable,
    per_page: int = 100,
    max_pages: int = 100
) -> Iterator[T]:
    """Generator that yields items from all pages."""
    cursor = None
    pages_fetched = 0

    while pages_fetched < max_pages:
        page = fetch_fn(per_page=per_page, cursor=cursor)
        yield from page.items

        pages_fetched += 1

        if not page.next_cursor:
            break
        cursor = page.next_cursor

@click.command()
@click.option('--per-page', default=50, help='Items per page')
@click.option('--cursor', help='Pagination cursor')
@click.option('--page', type=int, help='Page number (offset-based)')
@click.option('--all', 'fetch_all', is_flag=True, help='Fetch all pages')
@click.option('--max-pages', default=100, help='Max pages when using --all')
@click.option('--sort-by', default='created_at', help='Sort field')
@click.option('--sort-order', type=click.Choice(['asc', 'desc']), default='desc')
def list_items(per_page, cursor, page, fetch_all, max_pages, sort_by, sort_order):
    if fetch_all:
        items = list(fetch_all_pages(
            lambda **kw: api.list_items(**kw, sort_by=sort_by, sort_order=sort_order),
            per_page=per_page,
            max_pages=max_pages
        ))
        output_json({
            "ok": True,
            "result": {"items": items, "total": len(items), "has_more": False}
        })
    else:
        result = api.list_items(
            per_page=per_page,
            cursor=cursor,
            page=page,
            sort_by=sort_by,
            sort_order=sort_order
        )
        output_json(result)
```

## Async rate limiter

Contract: `../../cli/rate-limits.md`.

```python
import asyncio
import time
import click
from dataclasses import dataclass
from typing import Callable, TypeVar
import random

T = TypeVar('T')

@dataclass
class RateLimitOptions:
    rate_limit: str = "100/minute"  # e.g., "100/minute", "10/second"
    retry_on_rate_limit: bool = True
    max_retries: int = 5
    backoff_initial: float = 1.0
    backoff_max: float = 60.0
    backoff_multiplier: float = 2.0
    backoff_jitter: float = 0.1
    respect_retry_after: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 30.0

class RateLimiter:
    def __init__(self, options: RateLimitOptions):
        self.options = options
        self.tokens, self.interval = self._parse_rate_limit(options.rate_limit)
        self.available_tokens = self.tokens
        self.last_refill = time.monotonic()
        self.failures = 0
        self.circuit_open = False
        self.circuit_open_at = 0.0
        self._lock = asyncio.Lock()

    def _parse_rate_limit(self, rate: str) -> tuple[int, float]:
        count, period = rate.split('/')
        periods = {'second': 1, 'minute': 60, 'hour': 3600}
        return int(count), periods.get(period, 60)

    async def _acquire(self):
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.available_tokens = min(
                self.tokens,
                self.available_tokens + (elapsed / self.interval) * self.tokens
            )
            self.last_refill = now

            if self.available_tokens < 1:
                wait_time = (1 - self.available_tokens) * (self.interval / self.tokens)
                await asyncio.sleep(wait_time)
                self.available_tokens = 1

            self.available_tokens -= 1

    async def execute(self, fn: Callable[[], T]) -> T:
        # Check circuit breaker
        if self.circuit_open:
            if time.monotonic() - self.circuit_open_at > self.options.circuit_breaker_timeout:
                self.circuit_open = False
                self.failures = 0
            else:
                raise CircuitOpenError(
                    f"Circuit open, retry after {self.options.circuit_breaker_timeout - (time.monotonic() - self.circuit_open_at):.1f}s"
                )

        await self._acquire()

        backoff = self.options.backoff_initial
        last_error = None

        for attempt in range(self.options.max_retries + 1):
            try:
                result = await fn()
                self.failures = 0
                return result
            except RateLimitError as e:
                self.failures += 1
                if self.failures >= self.options.circuit_breaker_threshold:
                    self.circuit_open = True
                    self.circuit_open_at = time.monotonic()
                    raise CircuitOpenError("Too many failures, circuit opened")

                if not self.options.retry_on_rate_limit:
                    raise

                # Determine wait time
                wait_time = e.retry_after if self.options.respect_retry_after and e.retry_after else backoff

                # Add jitter
                if self.options.backoff_jitter > 0:
                    jitter = wait_time * self.options.backoff_jitter * (random.random() * 2 - 1)
                    wait_time += jitter

                await asyncio.sleep(wait_time)

                backoff = min(backoff * self.options.backoff_multiplier, self.options.backoff_max)
                last_error = e
            except Exception as e:
                self.failures += 1
                last_error = e
                if self.failures >= self.options.circuit_breaker_threshold:
                    self.circuit_open = True
                    self.circuit_open_at = time.monotonic()
                raise

        raise MaxRetriesExceeded(f"Max retries exceeded: {last_error}")

# CLI usage
@click.command()
@click.option('--rate-limit', default='100/minute')
@click.option('--retry-on-rate-limit', is_flag=True, default=True)
@click.option('--max-retries', default=5)
@click.option('--backoff-initial', default='1s')
@click.option('--backoff-max', default='60s')
@click.option('--backoff-multiplier', default=2.0)
@click.option('--respect-retry-after', is_flag=True, default=True)
@click.option('--circuit-breaker-threshold', default=5)
@click.option('--circuit-breaker-timeout', default='30s')
def sync(rate_limit, **kwargs):
    options = RateLimitOptions(rate_limit=rate_limit, **kwargs)
    limiter = RateLimiter(options)

    async def run():
        return await limiter.execute(api.sync)

    result = asyncio.run(run())
    output_json(result)
```
