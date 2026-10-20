# Keep the MCP server alive: no exits, lazy connections, lazy token checks

> Read when: you are writing server startup, a tool handler that can fail fatally, or code that opens a database, API client or credential at boot.

<!-- src: audit-agentic-mcp/references/patterns/transport-and-ops.md#5. Never Call process.exit() or sys.exit() Inside Tool Handlers -->
## Never exit the process inside a tool handler

Calling `process.exit()` (Node) or `sys.exit()` (Python) inside a tool handler kills the entire server process. The agent does not get a tool error; it gets a transport-level disconnection. It cannot retry, cannot fall back, cannot even tell the user what went wrong.

What the agent sees:

```
Agent -> call tool "deploy" -> transport error: connection reset
Agent -> retry? Server is gone. No tool listing available.
Agent -> "I'm unable to reach the MCP server."
```

The principle: if a tool cannot do its job, return `isError: true` with actionable guidance (for an invalid config: say the path is invalid or missing and what is expected, for example "Expected YAML with keys: host, port, db_name"). Keep the server alive so other tools remain available. Also wrap handlers so an unhandled exception becomes `Internal error: <type>: <message>` as a tool result rather than a crash. Code: [python](../frameworks/mcp-python/transport-and-ops.md).

Sources: Stainless, practitioner reports on software-architecture forums.

<!-- src: audit-agentic-mcp/references/patterns/transport-and-ops.md#6. Open External Connections Inside Tool Calls, Not at Startup -->
## Open external connections inside tool calls

Open database connections, API clients and external service handles inside each tool call, not at server startup. Accept the slight latency hit for dramatically higher reliability. A connection made at startup that throws means the server never registers its tools.

The trade-off is worth it:
- Tool listing always works, even when external services are down.
- Connection errors surface as structured tool errors the agent can reason about (for example "Database error: ... Check DATABASE_URL." with `isError: true`).
- Each tool is independently resilient: a broken database does not kill your file tools.
- Connection pooling can still be used; just initialize the pool lazily on first tool call.

For high-frequency tools, use a lazy singleton: initialize the connection on first use, cache it, and handle reconnection inside the tool if it goes stale. Close per-call connections in a `finally` block. Code: [typescript](../frameworks/mcp-ts/transport-and-ops.md).

Source: Docker blog (MCP server best practices).

<!-- src: audit-agentic-mcp/references/patterns/transport-and-ops.md#7. Validate Authentication Tokens at Execution Time, Not Startup -->
## Validate tokens when a tool needs them

Defer token validation to the moment a tool actually needs it. If you validate at startup, an expired or invalid token prevents the client from even discovering which tools exist (the server crashes before it is constructed).

Do instead: read the credential inside the handler; if it is missing return an actionable message ("API_TOKEN not set. Add it to your environment and restart the server."); on an upstream 401 return "Token expired or invalid. Re-authenticate at <settings URL>"; re-raise other errors.

What this buys you:
- Tool discovery always works regardless of auth state.
- Token errors are actionable instead of opaque connection failures.
- Tokens that rotate or expire mid-session are handled naturally.
- Tools with different auth requirements degrade independently.

The same principle applies to API keys, OAuth tokens, service account credentials and SSL certs. Code: [python](../frameworks/mcp-python/transport-and-ops.md). Token audience and passthrough rules: [security/auth-obo-and-token-passthrough.md](security/auth-obo-and-token-passthrough.md).

Source: Docker blog (MCP server best practices).
