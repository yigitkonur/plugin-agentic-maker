---
as_of: 2026-04
verify_before_citing: true
---

# Exemplar design disagreements and notable one-offs

> Read when: a principle looks settled but vendors split on it (tool count, naming, `structuredContent`, SSE, auth model, monolith vs mesh, static vs auto-registered tools) and you must choose deliberately; also for the list of distinctive one-off designs.

Overview: `exemplar-servers.md`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#5. Design disagreements -->
## Design disagreements

Seven places where the exemplars split.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Disagreement 1: Tool count — Cloudflare (2) vs GitHub (56) vs Atlassian Rovo (54) -->
### Disagreement 1: Tool count, Cloudflare (2) vs GitHub (56) vs Atlassian Rovo (54)

Cloudflare bets that Codemode dominates for large APIs: 2 tools, 1,000 tokens, JS sandbox. GitHub and Atlassian bet on rich discrete surfaces with toolset filtering as the lever. Both philosophies have live production deployments as of 2026-04. Vercel sits in the middle at exactly 14. Shopify Storefront lives at the other extreme (4 tools, workflow-consolidated). Copy whichever matches your domain: Codemode-friendly REST APIs, Cloudflare; product platform with strong resource nouns, GitHub/Atlassian; narrow task surface, Shopify. See `mcp/design-*` and `decisions/tool-count.md`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Disagreement 2: Naming — `snake_case` (almost everyone) vs `camelCase` (Atlassian Rovo) -->
### Disagreement 2: Naming, `snake_case` (almost everyone) vs `camelCase` (Atlassian Rovo)

Atlassian Rovo is the major outlier and pushes further with dotted sub-actions (`bitbucketPullRequest.merge`, `bitbucketRepoContent.branch.get`). Notion uses `kebab-case`. Everyone else ships `snake_case`. The risk with non-`snake_case` is accidental collisions with client tooling that assumes `snake_case` identifiers. If you break from `snake_case`, document it and avoid cross-tool name collisions. See `mcp/schemas-*`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Disagreement 3: `structuredContent` adoption vs stringified JSON -->
### Disagreement 3: `structuredContent` adoption vs stringified JSON

The MCP spec added `structuredContent` precisely to stop vendors shipping JSON-in-text. Yet Supabase's README states "this server does not send `structuredContent`; Vercel AI SDK parses JSON from content text." Linear ships the same way. Recommendation: send `structuredContent` and a human-readable text summary. Do not rely on JSON parsing from text; it breaks clients that respect the spec. See `mcp/responses-*`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Disagreement 4: Transport — Streamable HTTP only (HubSpot) vs + SSE fallback retained (Intercom, Notion) -->
### Disagreement 4: Transport, Streamable HTTP only (HubSpot) vs SSE fallback retained (Intercom, Notion)

HubSpot rejects SSE outright: "Supporting SSE would have introduced load balancer and scaling complexity" (`product.hubspot.com/blog/...`, 2025-06-18). Intercom and Notion keep a deprecated SSE endpoint alongside Streamable HTTP for backward compatibility. If you operate behind an auto-scaling load balancer, HubSpot's reasoning applies: do not ship SSE. If you need to support legacy MCP clients, keep SSE and mark it deprecated in docs. See `mcp/ops-*`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Disagreement 5: Auth model — Stripe Restricted Keys vs HubSpot OAuth 2.1 + PKCE with per-call permission intersection -->
### Disagreement 5: Auth model, Stripe Restricted Keys vs HubSpot OAuth 2.1 + PKCE with per-call permission intersection

Stripe delegates permissioning entirely to Restricted API Keys, with no MCP-level scopes. HubSpot intersects OAuth app scopes with live user permissions on every call, adding a few dozen ms latency but enforcing current permissions. Stripe's model is simpler for single-tenant; HubSpot's is correct for mutable-permission enterprises. See `mcp/security/*`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Disagreement 6: One-monolith MCP vs per-product mesh -->
### Disagreement 6: One-monolith MCP vs per-product mesh

Atlassian Rovo ships one server spanning Jira, Confluence, JSM, Bitbucket, Rovo code/shared, Teamwork Graph, and Compass: 54 tools, cross-product graph exposed via `getTeamworkGraphContext`. Cloudflare ships 16+ separate product servers, each at its own URL, each with its own auth scope. Atlassian wins on cross-product correlation (one tool call returns linked Jira + Confluence content); Cloudflare wins on blast radius (compromise of the DNS analytics server does not grant access to AI Gateway). Pick based on whether your product surfaces share a graph or are genuinely independent.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Disagreement 7: Static tool list vs auto-registered tool list -->
### Disagreement 7: Static tool list vs auto-registered tool list

HubSpot auto-registers any microservice RPC marked `@ChirpTool`. GitHub, Linear, and Vercel maintain hand-curated tool lists. Auto-registration lets the MCP scale with the org without central coordination; hand-curation forces a deliberate API design review per tool. HubSpot's approach only works because the Gateway intersects scopes per call; otherwise auto-registered tools would sprawl permissions.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#6. Notable one-offs -->
## Notable one-offs

- **GitHub `github_support_docs_search`:** the parameter description is itself a behavioral policy: "Input from the user about the question they need answered. This is the latest raw unedited user message. You should ALWAYS leave the user message as it is, you should never modify it." Description-as-enforcement. See `mcp/descriptions-*`.
- **GitHub Insiders channel:** toggle via URL `/insiders` or header `X-MCP-Insiders: true`. Two activation vectors for the same flag.
- **Cloudflare product mesh:** 16+ separate product MCP servers (docs, bindings, builds, observability, radar, containers, browser rendering, logpush, AI Gateway, AI Search, audit logs, DNS analytics, DEX, CASB, GraphQL, Agents SDK), one URL each. A per-product server mesh rather than a monolith.
- **HubSpot `@ChirpTool` auto-discovery:** any internal RPC annotated `@ChirpTool` is auto-registered as an MCP tool. The service catalog drives the tool surface.
- **Supabase `createToolSchemas()`:** a client-side helper mirrors the URL filter for TS type safety.
- **Notion-flavored Markdown:** introduced specifically for MCP, because hierarchical JSON blocks were too token-heavy.
- **Figma `generate_diagram`:** Mermaid to FigJam reverse bridge, no other vendor replicates.
- **Sentry `EMBEDDED_AGENT_PROVIDER`:** requires a caller-supplied LLM key; an embedded LLM inside the MCP for NL search.
- **Zapier dual-mode (Classic per-action + Agentic meta):** no other vendor exposes both modes in one server.
- **Shopify Storefront auth:** zero authentication, per-tenant URL pattern; policy answers explicitly gated by docs ("use only the provided answer").
- **Asana V2 RFC 8707 `resource` param:** tokens work only with the MCP server, not with the REST API; deliberate surface isolation.
- **HubSpot custom Streamable HTTP transport:** the Java MCP SDK lacked support at build time; HubSpot wrote a custom transport and committed to contribute it back upstream.
