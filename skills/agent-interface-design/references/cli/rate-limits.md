# Client-Side Rate Limiting

> Read when: a command calls a rate-limited API repeatedly and must throttle itself and back off on 429.

<!-- src: audit-agentic-cli/references/execution-patterns.md#11. Rate Limiting (Client-Side) | audit-agentic-cli/references/execution-patterns.md#Rate Limit Flags -->
## Flags

```bash
mycli sync \
  --rate-limit 100/minute \
  --retry-on-rate-limit \
  --max-retries 5 \
  --backoff-initial 1s \
  --backoff-max 60s \
  --backoff-multiplier 2.0 \
  --respect-retry-after                # Honor Retry-After header
```

<!-- src: audit-agentic-cli/references/execution-patterns.md#Rate Limit Flag Standards -->
## Flag standards

| Flag | Description | Default |
|------|-------------|---------|
| `--rate-limit <rate>` | Request rate (e.g., `100/minute`) | unlimited |
| `--retry-on-rate-limit` | Auto-retry on 429 | true |
| `--max-retries <n>` | Maximum retry attempts | 5 |
| `--backoff-initial <duration>` | Initial backoff delay | 1s |
| `--backoff-max <duration>` | Maximum backoff delay | 60s |
| `--backoff-multiplier <n>` | Exponential multiplier | 2.0 |
| `--backoff-jitter <ratio>` | Random jitter (0-1) | 0.1 |
| `--respect-retry-after` | Honor Retry-After header | true |
| `--circuit-breaker-threshold <n>` | Failures before circuit opens | 5 |
| `--circuit-breaker-timeout <duration>` | Time before retry after open | 30s |

Rate format is `<count>/<period>` with period `second`, `minute` or `hour`; the limiter is a token bucket whose burst equals the count. Wait time after a 429: the `Retry-After` value if honored (seconds or HTTP date), otherwise the current backoff, plus or minus jitter; then multiply the backoff by the multiplier up to `--backoff-max`. The circuit breaker is described in `retry.md`.

<!-- src: audit-agentic-cli/references/execution-patterns.md#Rate Limit Response -->
## Rate limit response

```json
{
  "ok": false,
  "error": {
    "class": "rate_limit",
    "code": "RATE_LIMITED",
    "message": "Rate limit exceeded",
    "retry_after": 45,
    "retry_after_unit": "seconds",
    "limit": {
      "requests_per_minute": 100,
      "remaining": 0,
      "reset_at": "2024-01-15T10:31:00Z"
    }
  },
  "retry": {
    "should_retry": true,
    "retry_after": "45s",
    "retry_command": "mycli sync --continue"
  }
}
```

The class is `rate_limit` (exit 7, retryable, `error.retry_after` in seconds). A fuller example with `details` is in `error-classes.md`.

Implementations: `../frameworks/go/execution-patterns-paging-rate.md`, `../frameworks/python/execution-patterns-paging-rate.md`, `../frameworks/node/execution-patterns-paging-rate.md`.
