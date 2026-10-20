---
as_of: 2026-04
verify_before_citing: true
---
# Cloudflare Workers for remote MCP servers

> Read when: you are hosting a remote MCP server on Cloudflare Workers and must choose stateful or stateless, control idle cost and CPU limits, pin data jurisdiction, or add OAuth.

Verify before citing: platform limits and prices change; check the vendor page.

Durable lesson: pick the primitive by whether each client needs durable per-session state; hibernate idle sessions; set the lowest CPU cap your tools need; add OAuth inside the same Worker when you have one or two integrations. Code is in `../frameworks/mcp-ts/deployment-platforms.md`. Generic rules are in `../mcp/ops-hosting-constraints.md`.

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#1. On Cloudflare Workers, Use `McpAgent` for Stateful, `createMcpHandler` for Stateless -->
## McpAgent or createMcpHandler

The Cloudflare MCP stack has two primitives. Pick based on whether each client needs durable per-session state.

- **`McpAgent`** (in the `agents` package): binds every MCP client to a dedicated Durable Object instance. State survives across requests, across hibernation, and across region failovers. Use for per-user memory, long-running conversations, or resumable tool calls.
- **`createMcpHandler`** (from `agents/mcp`, a subpath of the `agents` package): plain Workers handler. No Durable Object, no session memory, no hibernation. Use for tools that are fully idempotent and stateless.

`MyMCP.serve("/mcp")` serves Streamable HTTP. `MyMCP.serveSSE("/sse")` exists for legacy clients but is deprecated. Do not mount both unless you explicitly need backward compatibility.

Sources (accessed 2026-04): developers.cloudflare.com/agents/guides/remote-mcp-server/ and /agents/api-reference/mcp-agent-api/.

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#2. Use Durable Object WebSocket Hibernation to Stop Paying for Idle MCP Sessions -->
## WebSocket hibernation

Durable Objects charge per GB-second of wall-clock time they are in memory. A chatty MCP session that waits 10 minutes between tool calls bills for those 10 minutes unless you hibernate.

Hibernation evicts the Durable Object from memory while keeping the WebSocket connection open. When the next message arrives, the runtime rehydrates it and calls `deserializeAttachment()` to restore per-connection state. Billing pauses during the idle window. Opt the socket into hibernation with `this.ctx.acceptWebSocket(ws, ["session-tag"])` instead of `addEventListener("message")`.

- Footgun: `serializeAttachment()` has a **2,048-byte hard cap**. Anything larger goes in SQLite storage (`this.ctx.storage.sql`), not the attachment.
- Billing delta: a session with 60 s of active work and 10 min of idle per hour on a non-hibernating Durable Object bills about 11x the compute of the same session on a hibernating one.

Sources: developers.cloudflare.com/durable-objects/best-practices/websockets/ (compatibility date 2026-04-07); .../platform/pricing/ (accessed 2026-04).

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#3. Cloudflare Workers CPU Time is 30s by Default — Opt Into 5 Minutes for Long Tools -->
## CPU time limit

Workers measure **CPU time**, not wall-clock time. I/O waits (fetch, Durable Object storage, D1 queries) do not count, but a synchronous hot loop or CPU-bound tool burns the budget fast.

- Default: 30,000 ms CPU per invocation.
- Maximum: 300,000 ms (5 min); requires explicit opt-in in `wrangler.toml`.
- There is no wall-clock limit. A Worker can sit in `await fetch()` for hours if the upstream supports it.

```toml
# wrangler.toml
name = "my-mcp-server"
main = "src/index.ts"
compatibility_date = "2026-04-07"

[limits]
cpu_ms = 300000   # opt into 5 min CPU
```

Set the lowest value your real tools need. Lower `cpu_ms` caps your bill against runaway loops.

Sources: developers.cloudflare.com/changelog/post/2025-03-25-higher-cpu-limits/ (2025-03-25); .../workers/platform/limits/ (accessed 2026-04).

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#4. For Regulated Workloads on Cloudflare, Bind the McpAgent to the FedRAMP Jurisdiction -->
## FedRAMP and EU jurisdiction

Durable Objects support jurisdictional binding. `jurisdiction: "fedramp"` pins the object, and every byte of SQLite state it owns, to Cloudflare's FedRAMP Moderate data plane. `jurisdiction: "eu"` pins to the EU for GDPR residency.

```toml
# wrangler.toml
[[durable_objects.bindings]]
name = "MCP_OBJECT"
class_name = "MyMCP"
jurisdiction = "fedramp"
```

The code side (`env.MCP_OBJECT.jurisdiction("fedramp").idFromName(userId)`; FedRAMP namespaces never cross into non-FedRAMP regions) is in the TypeScript framework file.

Source: developers.cloudflare.com/durable-objects/reference/data-location/ (accessed 2026-04).

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#5. Wrap McpAgent in `workers-oauth-provider` for Full OAuth 2.1 Without a Separate Auth Server -->
## OAuth 2.1 with workers-oauth-provider

Cloudflare's `workers-oauth-provider` is a first-party library that gives you a conforming OAuth 2.1 authorization server inside the same Worker: Dynamic Client Registration (RFC 7591), PKCE, token introspection, and `tokenExchangeCallback` for upstream federation. You do not need Auth0, WorkOS, Stytch or Clerk to ship a remote MCP with auth. It integrates natively with GitHub, Google, Slack, Stytch, Auth0, WorkOS, and Cloudflare Access.

> Note: prefer Client ID Metadata Documents where the client supports them, keep DCR for clients without them, and detect which from the authorization-server metadata.

Sources: github.com/cloudflare/workers-oauth-provider v0.4.0 (2026-03-31); blog.cloudflare.com/building-ai-agents-with-mcp-authn-authz-and-durable-objects (accessed 2026-04).
