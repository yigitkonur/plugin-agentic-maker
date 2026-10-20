# Observing CLI Calls

> Read when: you are adding logging, metrics, tracing, health checks or alerts around the CLI invocations an agent makes.

TypeScript implementations are in `../frameworks/node/agent-integration-observability.md` and `../frameworks/node/agent-integration-health-alerting.md`. The caller can only observe the process boundary: the command, its duration, its exit code and the error envelope. Anything inside the CLI (its own spans, its own retries) is visible only if the CLI exposes it.

<!-- src: audit-agentic-cli/references/agent-integration.md#14. Observability | audit-agentic-cli/references/agent-integration.md#Structured Logging -->
## Structured logging

Log one record per invocation, at the level set by `LOG_LEVEL` (default `info`):

| Field | Meaning |
|-------|---------|
| `cmd` | The command array |
| `duration_ms` | Wall-clock duration |
| `exit_code` | Process exit code, when known |
| `ok` | Envelope `ok` |
| `error_code` | Envelope `error.code`, when present |

Levels: `debug` when the invocation starts, `info` on success, `warn` on a failed envelope, `error` (with the exception and `duration_ms`) when the wrapper itself throws. Never log secrets (see `auth-and-secrets.md`).

<!-- src: audit-agentic-cli/references/agent-integration.md#Metrics Collection -->
## Metrics

| Metric | Type | Labels |
|--------|------|--------|
| `cli_invocations_total` | counter | `command`, `status` (`success`/`failure`), `exit_code` (the error code, or `0`) |
| `cli_duration_seconds` | histogram | `command`; buckets 0.1, 0.5, 1, 2, 5, 10, 30, 60 |
| `cli_retries_total` | counter | `command`, `reason` |

Build the `command` label from the first three tokens joined with `_` (for example `mycli_task_start`). Expose the registry on a `/metrics` endpoint.

<!-- src: audit-agentic-cli/references/agent-integration.md#Distributed Tracing (OpenTelemetry) -->
## Distributed tracing

Wrap each call in a span named `cli.invoke` with attributes `cli.command` (the binary), `cli.subcommand` (tokens 1-2 of the argument list), `cli.args_count`, then `cli.ok` and `cli.error_code` after the call. On a failed envelope set the span status to ERROR with the error message; on an exception record it and set ERROR; always end the span.

Propagate the trace context to the CLI only if it supports it: pass `TRACE_ID` and `SPAN_ID` as environment variables (or headers, if the CLI forwards them).
<!-- src: audit-agentic-cli/references/agent-integration.md#Health Checks -->
## Health checks

Three probes, each with a 5000 ms timeout, using commands the CLI already has:

| Check | Command | Failure message |
|-------|---------|-----------------|
| `cli_accessible` | `mycli version --json` | "CLI not accessible" |
| `daemon_running` | `mycli daemon status --json` | "Daemon not responding" |
| `auth_valid` | `mycli account whoami --json` | "Auth check failed" |

Each check reports `status` (`pass`/`fail`), optional `latency_ms` and `message`. Overall `status`: `healthy` when none failed, `degraded` when at least one failed, `unhealthy` when all failed. Add an ISO `timestamp`.

<!-- src: audit-agentic-cli/references/agent-integration.md#Alerting Integration -->
## Alerting

Config: `webhook_url`, `threshold_errors_per_minute`, `threshold_latency_p99_ms`. Keep a sliding window of 60000 ms (60 s) of failures and latencies; record each invocation as `(ok, latency_ms)` and re-check after each one.

- `error_rate`: fire when the failures in the window exceed `threshold_errors_per_minute`; payload `errors_per_minute`, `threshold`.
- `high_latency`: only with at least 10 samples in the window; p99 is `sorted[floor(n * 0.99)]`; fire when it exceeds `threshold_latency_p99_ms`; payload `p99_latency_ms`, `threshold`.

POST `{alert_type, timestamp, data}` as JSON to the webhook.
