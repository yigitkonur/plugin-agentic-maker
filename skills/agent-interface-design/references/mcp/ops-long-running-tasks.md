# Return a task ID for long-running tool calls

> Read when: a tool call can take more than a few seconds, or a hosting platform caps request duration and you need the polling-tool pattern.

<!-- src: audit-agentic-mcp/references/patterns/session-and-state.md#2. Return Task IDs for Long-Running Operations -->
## Return a task ID and let the agent poll

When a tool call will take more than a few seconds, return a task ID immediately and let the model poll for results. This prevents blocking the conversation and avoids timeouts.

Why:
- Default tool call timeouts are typically 30-60 seconds.
- Long-running operations block the conversation.
- The model can do other work while waiting.
- Progress updates keep the user informed.

Implementation options:
- The framework's background-task support (FastMCP: `@mcp.tool(task=True)`, or `@mcp.tool(task=TaskConfig(mode="required"))` for fine-grained control); the framework handles the task lifecycle and the tool returns `status`, `result` and a `message`.
- A simple async queue with Redis/SQLite backing.
- A thread pool for CPU-bound work.

The tool description should say that it runs as a background task and returns a task ID immediately. Code: [python](../frameworks/mcp-python/session-and-state.md). Progress and cancellation of a running request: [protocol-progress-and-cancellation.md](protocol-progress-and-cancellation.md).

Sources: FastMCP tasks docs, FastMCP 3.0 release notes.

## Polling tool pattern

For work that outlives any request limit (a platform that caps duration, or a job of many minutes), do not hold the MCP request open:

1. The tool enqueues the job and returns at once a small JSON object, for example `{"jobId": "...", "status": "queued", "poll_tool": "get_index_status", "estimated_seconds": 180}`.
2. A separate worker does the work.
3. Expose a `get_*_status` tool that takes the `jobId` and returns `queued`, `running`, `completed` or `failed` plus the result or a recovery hint.
4. Optionally the worker also reports completion by webhook.

The MCP session never blocks on the long job. Platform limits that force this: [ops-hosting-constraints.md](ops-hosting-constraints.md).

> Reconciled: the platform source pointed to a polling-tool pattern in a file that does not exist; this section is that pattern and the pointer now targets it.
