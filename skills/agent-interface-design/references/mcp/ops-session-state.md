# Scope MCP server state to the session and pool connections

> Read when: you are deciding where an MCP server keeps state (pagination cursors, preferences, tokens), or how to raise throughput for a client that makes many calls.

<!-- src: audit-agentic-mcp/references/patterns/session-and-state.md#Session and State -->
Patterns for managing state across MCP sessions: scoping state correctly and scaling throughput with session pooling. Learning from successful calls and compaction are in [ops-success-log-and-compaction.md](ops-success-log-and-compaction.md); long-running operations are in [ops-long-running-tasks.md](ops-long-running-tasks.md). Code: [python](../frameworks/mcp-python/session-and-state.md), [typescript](../frameworks/mcp-ts/session-and-state.md).

<!-- src: audit-agentic-mcp/references/patterns/session-and-state.md#3. Scope State to Session, Not Global Variables -->
## Scope state to the session, never to module globals

When the server keeps state (auth tokens, pagination cursors, user preferences), key it to the session identifier. Never use module-level globals: a global page counter or token is shared by every active session and races when two sessions run at once.

- Bad: a global `current_page` incremented by `next_page`, and a global `auth_token`.
- Good: a dict keyed by `ctx.session_id` holding `page` and `prefs` (`timezone`, `language`) per session.

Where each kind of state lives:

| Lifetime | Examples | Store |
|---|---|---|
| Short-lived | pagination, current context | in-memory dict keyed by session ID |
| Medium-lived | user prefs, cached results | Redis with TTL |
| Long-lived | user quotas, history | database |

Clean up: set TTLs or implement session cleanup to prevent memory leaks. Treat session state like API state: create on first use, clear when done, never leak between users.

Sources: NearForm (Implementing MCP), FastMCP state docs. For rotating and binding session IDs see [security/oauth-scopes-ssrf-sessions.md](security/oauth-scopes-ssrf-sessions.md).

<!-- src: audit-agentic-mcp/references/patterns/session-and-state.md#4. Session Pooling for 10x Throughput -->
## Pool connections and externalize session state

A shared pool of about 10 sessions delivers roughly 8 to 10x the throughput of a unique session per request. The bottleneck is connection setup overhead (TLS handshake, protocol negotiation, state initialization); pooling amortizes it. A single stdio process is the slowest configuration measured.

Rules:
- Pool connections (example settings: min 2, max 10, idle timeout 60 s) and acquire/release around every call.
- Externalize session state (for example Redis with a 3600 s TTL under `session:<sid>`) so any pooled connection can serve any request.
- Pool connections, externalize state, let the pool handle lifecycle.

Benchmark rows (unique sessions, shared pool of 10, stdio): [fresh/mcp-transport-benchmarks.md](../fresh/mcp-transport-benchmarks.md). Scaling decisions: [../decisions/scaling.md](../decisions/scaling.md).

Source: Stacklok Kubernetes performance testing.
