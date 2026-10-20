# Add structured logs, metrics and health checks from day one

> Read when: you are putting an MCP server into production, deciding which metrics to emit, or adding a health endpoint or health tool.

<!-- src: audit-agentic-mcp/references/patterns/transport-and-ops.md#4. Add Structured Observability from Day One -->
## Log and measure every tool call

Servers in production need the same observability as any other service. Do not wait for problems to add logging and metrics.

Structured logging: one JSON object per tool call, written to stderr (never stdout; see [ops-stdio-hygiene.md](ops-stdio-hygiene.md)). Fields: `timestamp`, `level`, `event` (`tool_call`), `tool`, `params` (with sensitive fields removed), `success` (not `isError`), `duration_ms`, `tokens_estimate` (response JSON length divided by 4).

Key metrics to emit:
- `tool_call_count` by tool name (which tools are used most?)
- `tool_call_duration_seconds` histogram (are any tools slow?)
- `tool_error_count` by tool name and error type (which tools fail most?)
- `active_sessions` gauge (how many concurrent users?)
- `response_token_estimate` histogram (which tools produce the largest responses?)

Health checks: expose a `/health` HTTP route that checks each dependency (database, cache, external API) and returns `{"status": "healthy" | "degraded", "checks": {...}}`.

Non-obvious insight: track token estimates per response. A tool that returns 20k tokens on every call burns context window and money; the metric shows which tools need a `response_format` enum or pagination.

Code: [python](../frameworks/mcp-python/transport-and-ops.md).

Sources: modelcontextprotocol.io best practices, Pragmatic Engineer (MCP deep dive).

<!-- src: audit-agentic-mcp/references/patterns/transport-and-ops.md#11. Health Checks with KPI Targets -->
## Expose a structured health tool with KPI targets

Return per-component status and KPI metrics. This enables infrastructure monitoring, load-balancer routing and agent-driven diagnostics with a single tool.

The `health_check` tool ("Check server health and KPIs. Returns per-component status.") takes `include_metrics` (boolean, default false: "Set true to include request-rate and latency percentile metrics"). It checks the database, cache and upstream API concurrently (settled, so one failure does not hide the others). Each component reports `status` (`healthy`, `degraded` or `unhealthy`), optional `latency_ms`, `error` and `details`. Overall status: `unhealthy` if any component is unhealthy, `healthy` if all are, otherwise `degraded`. With metrics included, add `requests_per_second`, `p50_latency_ms`, `p95_latency_ms`, `p99_latency_ms`, `error_rate_percent` and a `kpi_targets` object (`target_rps` "> 1000", `target_p95_ms` "< 100", `target_error_rate` "< 0.1%"). The result also carries `uptime_seconds`.

Production KPI targets:

| KPI | Target | Why |
|---|---|---|
| Throughput | > 1,000 req/s | Handles bursty agentic loops |
| P95 latency | < 100ms | Keeps agentic sessions responsive |
| P99 latency | < 500ms | Prevents cascading timeouts |
| Error rate | < 0.1% | LLM context is not wasted on error recovery |
| Tool success rate | > 99% | Low failure rate means fewer retries |

Why it matters: agents that call tools blindly during a degraded server state waste context budget on retries. A structured health tool lets orchestrators skip to a fallback server or pause the session until degradation resolves. Code: [typescript](../frameworks/mcp-ts/transport-and-ops-health.md). Production gate: [../decisions/production-readiness.md](../decisions/production-readiness.md).

Sources: modelcontextprotocol.io observability guidance, Stacklok.
