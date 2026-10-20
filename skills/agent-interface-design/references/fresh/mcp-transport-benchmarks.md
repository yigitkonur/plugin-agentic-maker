---
as_of: 2026-07-04
verify_before_citing: true
---
# MCP transport and session-pool benchmarks (Kubernetes load tests)

> Read when: you need the measured numbers behind the advice to use Streamable HTTP with a shared session pool, or you are about to quote them.

The source gives no measurement date. It attributes both tables to Stacklok's performance testing of MCP servers in Kubernetes and cites the MCP specification revision 2025-11-25 for the transport definitions. Treat the figures as one team's test setup, not a guarantee. Rules derived from them: [ops-transport-selection.md](../mcp/ops-transport-selection.md), [ops-session-state.md](../mcp/ops-session-state.md).

<!-- src: audit-agentic-mcp/references/patterns/transport-and-ops.md#8. Transport Choice Makes or Breaks Performance -->
## Transport comparison

| Transport | Concurrency | Success % | Req/s | Avg Response Time |
|---|:---:|:---:|:---:|:---:|
| stdio | 20 | 4% | 0.64 | 20s |
| SSE | 20 | 100% | 7.23 | 18ms |
| Streamable HTTP (shared pool) | 20 | 100% | 48.4 | 5ms |
| Streamable HTTP (shared pool) | 200 | 100% | 299.85 | 622ms |

Reading: stdio serializes every request through one process, so at concurrency 20 most requests time out and only 4% succeed. Streamable HTTP with a shared session pool gives about 300 req/s at concurrency 200. That is about 6.2x the 20-concurrency throughput for 10x the concurrency, so it scales well but not linearly.

<!-- src: audit-agentic-mcp/references/patterns/session-and-state.md#4. Session Pooling for 10x Throughput -->
## Session pooling comparison

| Configuration | Req/s | Avg Response |
|---|---|---|
| Unique sessions | 30-36 | 500ms+ |
| Shared pool (10) | 290-300 | 5ms |
| stdio (single) | 0.64 | 20s |

The source headline says a shared pool of 10 sessions gives "~10x" throughput over a unique session per request. From the rows above it is about 8 to 10x (290-300 divided by 30-36). The bottleneck is connection setup overhead (TLS handshake, protocol negotiation, state initialization); pooling amortizes it.
