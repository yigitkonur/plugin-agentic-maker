---
as_of: unknown
verify_before_citing: true
---

# Gateways and aggregators: MetaMCP, MCPJungle, Portkey, Cloudflare, Glama

> Read when: you pick a gateway to put N MCP servers behind one controlled endpoint and need each product's auth, namespace strategy, and fit. Verify before citing.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#2. Gateways / Aggregators — the Request-Path Tier -->
## Gateways: the request-path tier

Gateways consume registries and upstreams; they do not replace them. The generic meta-server pattern is in `mcp/design-*` (composition). The profiles below are the concrete products most operators compare in 2025-26.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#MetaMCP (metatool-ai) -->
## MetaMCP (metatool-ai)

Open-source aggregator, orchestrator, and gateway. Proxies N upstream servers into one unified server with middleware.

- **Trust:** Better Auth for frontend/backend; internal proxy uses session cookies; external access uses API keys via `Authorization: Bearer`; MCP OAuth spec 2025-06-18 compliant; OIDC SSO with PKCE; multi-tenant public/private scopes. Public API keys cannot access private MetaMCPs (docs.metamcp.com, 2025).
- **Namespace collision handling:** tools auto-prefixed `{ServerName}__{originalToolName}`.
- **Middleware:** pluggable for logging, filtering, scanning.
- **Pricing:** free OSS; self-host.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#MCPJungle -->
## MCPJungle

Self-hosted gateway for private agent fleets. Single `/mcp` endpoint proxies many registered servers; supports Tool Groups.

- **Trust:** self-hosted; static bearer token for Streamable HTTP upstreams; upstream OAuth "coming soon."
- **Naming:** `<mcp-server-name>__<tool-name>` (aligned with MetaMCP deliberately).
- **Enterprise:** OpenTelemetry observability (github.com/mcpjungle/MCPJungle, 2025).

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#Portkey MCP Gateway -->
## Portkey MCP Gateway

Enterprise control plane: "Unified layer to access and govern MCP tools without modifying your agents or servers."

- **Trust:** OAuth 2.1 + API tokens + header auth; JWT validation with identity forwarding; credentials never leave the gateway; BYO IdP (Okta, Entra, Auth0) (portkey.ai/features/mcp; docs.portkey.ai/docs/product/mcp-gateway, 2025).
- **Namespace:** `https://mcp.portkey.ai/{server-slug}/mcp`.
- **Observability:** end-to-end traces, per-tool logs, filterable by server/user/time.
- **Adoption:** "3,000+ GenAI teams."

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#Cloudflare AI Gateway + Remote MCP + Enterprise Reference -->
## Cloudflare AI Gateway, Remote MCP, enterprise reference

Three stacked products, each independently useful:

1. **Cloudflare's own MCP catalog:** 10+ product servers at `mcp.cloudflare.com`, `docs.mcp.cloudflare.com`, `bindings.mcp.cloudflare.com`, `observability.mcp.cloudflare.com`. The Cloudflare-API MCP compresses 2,500+ REST endpoints into 2 tools (`search()` + `execute()`) via the Codemode pattern in an isolated Dynamic Worker sandbox (Workers substrate: `mcp/ops-*`). The exemplar survey counts 16+ product servers (`exemplar-servers-developer-platforms.md`).
2. **Remote MCP on Workers:** `workers-oauth-provider` makes a Worker both OAuth provider (to the MCP client) and OAuth client (to upstream). Implements RFC 7591 DCR + RFC 8414 AS Metadata (developers.cloudflare.com/agents/model-context-protocol/mcp-servers-for-cloudflare/, 2025). Upstream tokens encrypted in Workers KV, never exposed to the client.
3. **Enterprise reference architecture:** Cloudflare Access as OAuth provider, MCP portals revealing authorized servers, default-deny write; Gateway inspects/logs/blocks/redirects MCP JSON-RPC; Code Mode activated by appending `?codemode=search_and_execute` (blog.cloudflare.com/enterprise-mcp/, 2025).

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#Glama Gateway -->
## Glama Gateway

Same product as the Glama registry: the quality score runs on gateway traffic, the gateway logs every call. Supports OAuth 2.1 DCR.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#Gateway comparison — when each one fits -->
## Gateway comparison: when each one fits

| Need | MetaMCP | MCPJungle | Portkey | Cloudflare | Glama Gateway |
|---|---|---|---|---|---|
| Self-host required | Yes | Yes | Optional (SaaS default) | Yes (Workers) | No (SaaS) |
| Multi-tenant public/private scopes | Yes | Limited | Yes | Via Access | No |
| OAuth 2.1 DCR | Partial | Coming | Yes | Yes (reference impl) | Yes |
| Built-in observability | OTel-ready | OTel (enterprise) | First-class traces | Gateway logs + analytics | Per-call audit |
| Network edge | Operator's infra | Operator's infra | Portkey edge | Cloudflare global | Glama cloud |
| Namespace strategy | `{Server}__{tool}` | `{server}__{tool}` | `{slug}` in URL | Product subdomains | Repo path |

If the operator already runs a control plane (Okta/Entra + Gateway/API Gateway), MetaMCP or Portkey slot in cleanly. If the operator runs on Cloudflare's edge, `workers-oauth-provider` saves building OAuth from scratch. If the operator wants a quality signal surfaced to consumers, Glama is the only gateway that publishes one. DCR/CIMD stance: prefer CIMD where the client supports it, keep DCR for clients without it, detect from authorization-server metadata (`mcp/security/*`).
