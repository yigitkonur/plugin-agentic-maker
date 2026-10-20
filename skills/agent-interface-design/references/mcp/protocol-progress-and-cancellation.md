# Progress notifications and cooperative cancellation

> Read when: a tool runs longer than about a second and you are adding progress reporting, or a client cancel leaves your handler running.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 8: Progress Tokens Belong In `params._meta`, Not `params` -->
## Progress tokens live in params._meta

Rule: the requester puts `progressToken` in `params._meta.progressToken`. The notifier sends `notifications/progress` carrying that token at the top level of the notification params. `progress` MUST increase monotonically. Stop sending after the request completes. Never reuse a token across concurrent requests.

Putting `progressToken` at `params.progressToken` is a common silent bug; the spec only accepts `_meta.progressToken`. Flooding notifications violates the spec's SHOULD-rate-limit clause, and some clients drop the connection under load; very few clients support notifications at all (`../fresh/mcp-advanced-feature-support.md`). Treat progress as advisory UX only and never rely on it for correctness.

Request shape (the one neutral example):

```json
{"method": "tools/call",
 "params": {"_meta": {"progressToken": "abc123"}, "name": "long_task", "arguments": {}}}
```

The server reports `progress` (1..total), `total` and a `message` per chunk; frameworks read the token from `_meta` automatically. Code: `../frameworks/mcp-python/advanced-protocol.md`.

When NOT to use: fast operations (under 1 s), where overhead exceeds benefit; stateless HTTP mode with an ephemeral worker, which has no channel for asynchronous notifications (`protocol-capability-gating.md`). For work that takes minutes, return a task ID instead: `ops-long-running-tasks.md`.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 9: Handle `notifications/cancelled` Cooperatively — And Never Cancel `initialize` Or Tasks -->
## Handle notifications/cancelled cooperatively

Rule: on receiving `notifications/cancelled` with a matching `requestId`, stop processing, free resources and do NOT send a response. The sender SHOULD ignore any response that arrives after cancellation. For Tasks-primitive requests use `tasks/cancel` instead; `notifications/cancelled` is for regular requests only.

Uncancellable handlers make cancellation meaningless. A handler that calls blocking `time.sleep(60)` or synchronous HTTP cannot be interrupted, so the client sees the cancel acknowledged while the server burns resources for another minute. Cooperative async code with periodic cancel checks (raise a cancelled error at each loop iteration) is the only reliable implementation. The spec also forbids cancelling the `initialize` request (client to server) and requires that `notifications/cancelled` only reference requests sent in the same direction. Code: `../frameworks/mcp-python/advanced-protocol.md`.

When NOT to use: you are implementing the Tasks primitive (send `tasks/cancel`); the request has already completed (the spec says the receiver MAY ignore it). Revision detail: `../fresh/mcp-advanced-feature-revisions.md`.

Sources: MCP specification (progress, cancellation).
