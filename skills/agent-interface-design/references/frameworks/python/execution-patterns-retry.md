# Python: Idempotency Keys and Retry

> Read when: you are implementing idempotent creates or retry with backoff and Retry-After in a Python CLI.

## Idempotency store

Contract: `../../cli/idempotency.md`. Cached results live 24 hours.

```python
import json
import click
import redis
from typing import Optional

class IdempotencyStore:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.ttl = 86400  # 24 hours

    def get_or_execute(self, key: str, operation: callable) -> dict:
        # Check cache
        cached = self.redis.get(f"idempotency:{key}")
        if cached:
            return json.loads(cached)

        # Execute operation
        result = operation()

        # Cache result
        self.redis.setex(
            f"idempotency:{key}",
            self.ttl,
            json.dumps(result)
        )
        return result

# CLI usage
@click.command()
@click.option('--idempotency-key', help='Key for idempotent retry')
@click.option('--name', required=True)
def create(idempotency_key: Optional[str], name: str):
    def do_create():
        return api.create_resource(name=name)

    if idempotency_key:
        result = idempotency_store.get_or_execute(idempotency_key, do_create)
    else:
        result = do_create()

    output_json(result)
```

<!-- src: audit-agentic-cli/references/execution-patterns.md#Python Retry Implementation -->
## Retry

Contract and defaults: `../../cli/retry.md`.

```python
import sys
import time
import random
from functools import wraps
from typing import Callable, Type, Tuple
from dataclasses import dataclass
import httpx

@dataclass
class RetryConfig:
    max_attempts: int = 5
    initial_backoff: float = 0.1
    max_backoff: float = 30.0
    backoff_factor: float = 2.0
    jitter: float = 0.2
    retryable_exceptions: Tuple[Type[Exception], ...] = (
        httpx.TimeoutException,
        httpx.NetworkError,
    )
    retryable_status_codes: Tuple[int, ...] = (429, 500, 502, 503, 504)

class RetryExhausted(Exception):
    def __init__(self, last_error: Exception, attempts: int):
        self.last_error = last_error
        self.attempts = attempts
        super().__init__(f"Retry exhausted after {attempts} attempts: {last_error}")

def with_retry(config: RetryConfig = None):
    config = config or RetryConfig()

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except config.retryable_exceptions as e:
                    last_error = e
                except httpx.HTTPStatusError as e:
                    if e.response.status_code not in config.retryable_status_codes:
                        raise
                    last_error = e

                    # Honor Retry-After header
                    retry_after = e.response.headers.get("Retry-After")
                    if retry_after:
                        try:
                            backoff = min(float(retry_after), config.max_backoff)
                            time.sleep(backoff)
                            continue
                        except ValueError:
                            pass

                # Calculate backoff
                backoff = min(
                    config.initial_backoff * (config.backoff_factor ** attempt),
                    config.max_backoff
                )
                # Add jitter
                jitter = backoff * config.jitter * (random.random() * 2 - 1)
                backoff += jitter

                time.sleep(backoff)

            raise RetryExhausted(last_error, config.max_attempts)

        return wrapper
    return decorator

# Usage: a retried create carries the same Idempotency-Key on every attempt
@with_retry(RetryConfig(max_attempts=3))
def create_resource(name: str, idempotency_key: str) -> dict:
    response = httpx.post(f"{API_URL}/resources", json={"name": name},
                          headers={"Idempotency-Key": idempotency_key})
    response.raise_for_status()
    return response.json()

try:
    output_json(create_resource("demo", idempotency_key))
except RetryExhausted as e:
    # retryable failure with the budget spent: envelope on stdout, exit 7 (transient)
    output_json({"ok": False, "error": {"class": "network", "code": "RETRY_EXHAUSTED",
                 "message": str(e), "retryable": True, "suggestion": "Retry later"}})
    sys.exit(7)
```
