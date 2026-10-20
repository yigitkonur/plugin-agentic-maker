# Namespacing custom _meta keys

> Read when: you are adding trace IDs, tenant IDs or experimental fields to MCP requests, results or notifications through `_meta`.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 10: Namespace Custom `_meta` Keys With Reverse-DNS; Reserve Un-Namespaced For The Protocol -->
## Reverse-DNS keys, no secrets

Rule: every request, result and notification MAY carry `_meta`. The only reserved un-namespaced key is `progressToken` (backwards compatibility). A key's prefix is optional; when present it is dot-separated labels followed by `/`, and the spec says to use reverse DNS (`com.example/traceId`, `com.mycorp/tenant-id`). Any prefix whose second label is `modelcontextprotocol` or `mcp` (`io.modelcontextprotocol/`, `dev.mcp/`) is reserved for the spec; `com.example.mcp/` is not. Do not put secrets in `_meta`: it is unauthenticated.

Un-namespaced custom keys (`tenant_id`, `trace`) break once the spec adopts a conflicting name. `_meta` is the canonical carrier for `progressToken`, trace IDs, tenant IDs, experimental features before they reach the spec, and client build numbers for observability. Clients MAY strip unknown `_meta` keys, so never rely on round-trip guarantees. The rules were formalised by a spec enhancement proposal (see `../fresh/mcp-advanced-feature-revisions.md`).

Trace propagation pattern: read `com.acme/trace-id` from the request meta (or mint one), log it, pass it to the backend, and set it plus `com.acme/backend-version` on the result meta; clients MAY relay it. Code: `../frameworks/mcp-python/advanced-protocol.md`.

When NOT to use: storing tokens, API keys or PII. `_meta` is not authenticated, is not encrypted beyond TLS and may be logged by clients. For secrets use URL-mode elicitation (`protocol-elicitation.md`).

Sources: MCP specification changelog.
