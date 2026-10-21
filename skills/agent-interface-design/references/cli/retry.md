# Retry Strategy

> Read when: you are deciding which failures an agent or the CLI itself should retry, and with what backoff.

<!-- src: audit-agentic-cli/references/execution-patterns.md#2. Retry Logic | audit-agentic-cli/references/execution-patterns.md#Retry Classification -->
## Retry classification

| Error Class | Retry? | Strategy | Example |
|-------------|--------|----------|---------|
| exit-7 group (`transient`) | Yes | Exponential backoff | Temporary server issue |
| `rate_limit` | Yes | Honor Retry-After | 429 Too Many Requests |
| `timeout` | Yes | With jitter | Request timeout |
| `network` | Yes | With jitter | Connection refused |
| `conflict` | Maybe | Re-read, re-apply | Optimistic lock failure |
| `validation` | No | Fail fast | Invalid input |
| `auth` | No | Fail fast | Unauthorized |
| `not_found` | No | Fail fast | Resource doesn't exist |

> Note: `transient` is the name of the exit-7 group (`rate_limit`, `timeout`, `network`, `dependency_failed`), not an error class. See `error-classes.md`.

Defaults used by the reference implementations in every language:

| Setting | Value |
|---------|-------|
| Max attempts | 5 |
| Initial backoff | 100 ms |
| Max backoff | 30 s |
| Backoff factor | 2.0 |
| Jitter | 0.2 (plus or minus 20 percent of the backoff) |
| Retry-After | when the response carries one (seconds, or an HTTP date), wait that long instead of the computed backoff |
| Retryable HTTP statuses | 429, 500, 502, 503, 504 |

Rules:

- A non-retryable error returns immediately; only classes marked retryable loop.
- Honor context cancellation and deadlines between attempts.
- A `conflict` is retried only after re-reading state.
- Retry only idempotent operations, or ones carrying an idempotency key (`idempotency.md`).

Client-side rate-limit flags and their own backoff defaults (1 s initial, 60 s max, multiplier 2.0, jitter 0.1) are in `rate-limits.md`.

Implementations: `../frameworks/go/execution-patterns-retry.md`, `../frameworks/python/execution-patterns-retry.md`, `../frameworks/node/execution-patterns-retry.md`.

<!-- src: audit-agentic-cli/references/execution-patterns.md#Circuit Breaker Pattern -->
## Circuit breaker

Stop retrying after repeated failures. A breaker has three states: `closed` (normal), `open` (fail fast without calling), `half-open` (one trial after the reset timeout).

- After `maxFailures` consecutive failures the breaker opens and stamps the time of the last failure.
- While open, calls return a "circuit breaker open" error until `resetTimeout` has passed, then the breaker goes half-open.
- A success resets the failure count and closes the breaker; a failure in half-open reopens it.
- Flag defaults: `--circuit-breaker-threshold` 5 and `--circuit-breaker-timeout` 30s (see `rate-limits.md`).

Go implementation: `../frameworks/go/execution-patterns-retry.md`.
