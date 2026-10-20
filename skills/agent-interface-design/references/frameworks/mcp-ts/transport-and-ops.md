# TypeScript: stderr logger, lazy connections, affinity and graceful shutdown

> Read when: you are writing the Node/TypeScript side of an MCP server's logging, per-call connections, Kubernetes session affinity or SIGTERM handling.

Rules: [ops-stdio-hygiene.md](../../mcp/ops-stdio-hygiene.md), [ops-server-resilience.md](../../mcp/ops-server-resilience.md), [ops-kubernetes.md](../../mcp/ops-kubernetes.md). Siblings: [rate limiting](transport-and-ops-rate-limiting.md), [caching](transport-and-ops-caching.md), [health tool](transport-and-ops-health.md).

<!-- src: audit-agentic-mcp/references/patterns/transport-and-ops.md#1. Keep stdout Pure JSON-RPC -- All Logs to stderr -->
## Node logger that writes to stderr

```javascript
const logger = {
    info: (msg, data) => console.error(`[INFO] ${msg}`, data ?? ''),
    error: (msg, err) => console.error(`[ERROR] ${msg}`, err?.stack || err || '')
};

// NEVER use console.log() in an MCP server
// Use console.error() or the logger
logger.info("Server started");
```

<!-- src: audit-agentic-mcp/references/patterns/transport-and-ops.md#6. Open External Connections Inside Tool Calls, Not at Startup -->
## Connect per tool call

Wrong, connection at startup blocks everything:

```typescript
// Server fails to start if DB is down
const db = new Pool({ connectionString: process.env.DATABASE_URL });
await db.connect(); // Throws -> server never registers tools

const server = new McpServer({ name: "analytics" });
server.tool("query_metrics", schema, async (params) => {
  const result = await db.query(params.sql);
  return { content: [{ type: "text", text: JSON.stringify(result.rows) }] };
});
```

Right, connect per tool call:

```typescript
const server = new McpServer({ name: "analytics" });

server.tool("query_metrics", schema, async (params) => {
  let db;
  try {
    db = new Pool({ connectionString: process.env.DATABASE_URL });
    const result = await db.query(params.sql);
    return { content: [{ type: "text", text: JSON.stringify(result.rows) }] };
  } catch (err) {
    return {
      content: [{ type: "text", text: `Database error: ${err.message}. Check DATABASE_URL.` }],
      isError: true,
    };
  } finally {
    await db?.end();
  }
});
```

<!-- src: audit-agentic-mcp/references/patterns/transport-and-ops.md#12. Kubernetes Deployment for MCP Servers -->
## Session affinity and graceful shutdown

Session affinity for stateful servers (Service spec):

```yaml
apiVersion: v1
kind: Service
spec:
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 3600  # 1 hour session stickiness
```

Graceful shutdown, handle SIGTERM to complete in-flight tool calls:

```typescript
process.on("SIGTERM", async () => {
  await server.close();   // Stop accepting new connections
  await drainInflight();  // Wait for active tool calls to complete
  process.exit(0);
});
```
