# TypeScript: session pool, externalized state and compaction

> Read when: you are implementing a pooled MCP client session, Redis-backed session state, or priority-based conversation compaction in TypeScript.

Rules: [ops-session-state.md](../../mcp/ops-session-state.md), [ops-success-log-and-compaction.md](../../mcp/ops-success-log-and-compaction.md).

<!-- src: audit-agentic-mcp/references/patterns/session-and-state.md#4. Session Pooling for 10x Throughput -->
## Session pool and externalized state

```typescript
import { createPool } from "generic-pool";

const sessionPool = createPool({
  create: async () => {
    const session = await mcpClient.connect(serverUrl);
    await session.initialize();
    return session;
  },
  destroy: async (session) => await session.close(),
}, { min: 2, max: 10, idleTimeoutMs: 60_000 });

async function callTool(name: string, args: Record<string, unknown>) {
  const session = await sessionPool.acquire();
  try {
    return await session.callTool({ name, arguments: args });
  } finally {
    sessionPool.release(session);
  }
}
```

Externalize session state so any pooled connection can serve any request:

```typescript
await redis.setex(`session:${sid}`, 3600, JSON.stringify(state));
const state = JSON.parse(await redis.get(`session:${sid}`));
```

<!-- src: audit-agentic-mcp/references/patterns/session-and-state.md#5. Conversation Compaction Priorities -->
## Compaction cache and message classifier

Cache compaction with a content hash:

```typescript
import { createHash } from "crypto";

async function getCompactedContext(messages: Message[]): Promise<string> {
  const hash = createHash("sha256")
    .update(messages.map(m => m.content).join("|"))
    .digest("hex");
  const cached = await redis.get(`compaction:${hash}`);
  if (cached) return cached; // O(1) reuse
  const compacted = await summarize(messages);
  await redis.setex(`compaction:${hash}`, 3600, compacted);
  return compacted;
}
```

Classify at creation time:

```typescript
function classifyMessage(msg: McpMessage): Priority {
  if (msg.type === "schema" || msg.type === "tool_definition") return "anchor";
  if (msg.type === "tool_result" && msg.content.length > 500)  return "important";
  if (msg.type === "tool_result")                              return "contextual";
  if (msg.role === "assistant" && msg.content.length < 20)     return "transient";
  return "routine";
}
```
