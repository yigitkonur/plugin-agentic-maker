# Choose the MCP transport: stdio, Streamable HTTP, never new SSE

> Read when: you are picking a transport for a new MCP server, deciding how to deploy it remotely, or reviewing a server that still uses SSE.

<!-- src: audit-agentic-mcp/references/patterns/transport-and-ops.md#Transport and Operations -->
Patterns for production-grade server deployment. Siblings: [ops-stdio-hygiene.md](ops-stdio-hygiene.md), [ops-dev-loop.md](ops-dev-loop.md), [ops-observability.md](ops-observability.md), [ops-server-resilience.md](ops-server-resilience.md), [ops-rate-limiting-and-caching.md](ops-rate-limiting-and-caching.md), [ops-kubernetes.md](ops-kubernetes.md), [ops-session-state.md](ops-session-state.md).

<!-- src: audit-agentic-mcp/references/patterns/transport-and-ops.md#2. Use Streamable HTTP, Not Deprecated SSE -->
## Use Streamable HTTP for remote, stdio for local

The SSE (Server-Sent Events) transport is deprecated. New servers use Streamable HTTP for remote connections and stdio for local ones.

| Scenario | Transport | Why |
|----------|-----------|-----|
| Local tool (same machine) | `stdio` | Simplest, no network overhead |
| Remote server | Streamable HTTP | Bidirectional, supports streaming, future-proof |
| Browser client | Streamable HTTP | Works with standard HTTP infrastructure |
| Legacy integration | SSE (if forced) | Only if the client does not support Streamable HTTP yet |

Streamable HTTP advantages over SSE:
- Bidirectional communication (SSE is server-to-client only).
- Works with standard HTTP load balancers and proxies.
- Supports proper session management.
- Compatible with OAuth authentication flows.
- Better suited for production deployment behind CDNs.

When deploying remotely:
- Put it behind a reverse proxy (nginx, Caddy).
- Enable HTTPS (required for production).
- Set appropriate CORS headers for browser clients.
- Configure session affinity in load balancers (or externalize state; see [ops-session-state.md](ops-session-state.md)).

Code to select a transport: [python](../frameworks/mcp-python/transport-and-ops.md). Which clients still need SSE or lack Streamable HTTP: [../fresh/client-compatibility.md](../fresh/client-compatibility.md). Spec revision cited by the source: see the note in [../fresh/mcp-transport-benchmarks.md](../fresh/mcp-transport-benchmarks.md).

Sources: NearForm, MCP specification (transports).

<!-- src: audit-agentic-mcp/references/patterns/transport-and-ops.md#8. Transport Choice Makes or Breaks Performance -->
## Transport decides whether production concurrency works at all

Transport selection is not a minor config decision. Load testing in Kubernetes showed stdio collapsing at concurrency 20 (4% success), SSE working but slow, and Streamable HTTP with a shared session pool holding 100% success up to concurrency 200. All rows: [../fresh/mcp-transport-benchmarks.md](../fresh/mcp-transport-benchmarks.md).

Why stdio collapses under concurrency: a single process with stdin/stdout pipes serializes every request; at concurrency 20 requests queue behind each other, most time out. It is designed for single-user local development only.

Why Streamable HTTP wins:
- Shared session pooling amortizes connection overhead.
- The stateless request/response model maps naturally to HTTP load balancing.
- Standard infrastructure (reverse proxies, Kubernetes ingress, health checks) works out of the box.
- It scales well: about 300 req/s at concurrency 200 with sub-second response times.

Recommendation:

```
Local dev, single user     -> stdio is fine
Shared team server         -> Streamable HTTP
Production / multi-tenant  -> Streamable HTTP + session pooling + load balancer
```

If you are building a new server today, start with Streamable HTTP. The migration cost from stdio to HTTP later is non-trivial: you will need to rethink session management, add health endpoints, and handle concurrent state. Pooling rules: [ops-session-state.md](ops-session-state.md). Platform limits: [ops-hosting-constraints.md](ops-hosting-constraints.md).

Source: Stacklok (performance testing MCP servers in Kubernetes).
