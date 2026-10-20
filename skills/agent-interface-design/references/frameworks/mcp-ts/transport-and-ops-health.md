# TypeScript: health_check tool with KPI targets

> Read when: you are implementing the structured health_check tool for an MCP server in TypeScript.

Rules and KPI table: [ops-observability.md](../../mcp/ops-observability.md).

<!-- src: audit-agentic-mcp/references/patterns/transport-and-ops.md#11. Health Checks with KPI Targets -->
## Health tool

```typescript
import { z } from "zod";

interface ComponentHealth {
  status: "healthy" | "degraded" | "unhealthy";
  latency_ms?: number;
  error?: string;
  details?: Record<string, unknown>;
}

server.registerTool("health_check", {
  description: "Check server health and KPIs. Returns per-component status.",
  inputSchema: {
    include_metrics: z.boolean().default(false)
      .describe("Set true to include request-rate and latency percentile metrics"),
  },
}, async ({ include_metrics }) => {
  const [dbHealth, cacheHealth, upstreamHealth] = await Promise.allSettled([
    checkDatabase(),
    checkRedis(),
    checkUpstreamAPI(),
  ]);

  const components: Record<string, ComponentHealth> = {
    database: resolveHealth(dbHealth),
    cache: resolveHealth(cacheHealth),
    upstream_api: resolveHealth(upstreamHealth),
  };

  const allHealthy = Object.values(components).every(c => c.status === "healthy");
  const anyUnhealthy = Object.values(components).some(c => c.status === "unhealthy");

  const result: Record<string, unknown> = {
    status: anyUnhealthy ? "unhealthy" : allHealthy ? "healthy" : "degraded",
    components,
    uptime_seconds: process.uptime(),
  };

  if (include_metrics) {
    result.metrics = {
      requests_per_second: metrics.rps,
      p50_latency_ms: metrics.p50,
      p95_latency_ms: metrics.p95,
      p99_latency_ms: metrics.p99,
      error_rate_percent: metrics.errorRate,
    };
    result.kpi_targets = {
      min_rps: 1000,
      max_p95_ms: 100,
      max_error_rate_percent: 0.1,
    };
  }

  return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
});
```
