---
as_of: 2026-04
verify_before_citing: true
---

# Exemplar anti-patterns to avoid (Avoid 1 to 8)

> Read when: you are about to generate tools from OpenAPI, hand out manual OAuth tokens, remove tools silently, return stringified JSON, or ship without DCR, and want the public failure data behind each warning.

Overview and profiles: `exemplar-servers.md`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#4. Avoid-this anti-patterns -->
## Avoid-this anti-patterns

Eight patterns with public failure data.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Avoid 1: Notion v1 — 1:1 OpenAPI → MCP generation -->
### Avoid 1: Notion v1, 1:1 OpenAPI to MCP generation

Notion's post-mortem (`notion.com/blog/notions-hosted-mcp-server-an-inside-look`, 2026): "1:1 API-to-tool mapping produced poor agent experiences, including high token use from hierarchical JSON block data." v2 added hand-written AI-first tools and introduced Notion-flavored Markdown because JSON blocks burned tokens. If you are shipping v1, stop: every exemplar that started API-shaped migrated away from it.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Avoid 2: PayPal — manual OAuth `client_credentials` flow in MCP config -->
### Avoid 2: PayPal, manual OAuth `client_credentials` flow in MCP config

PayPal ships an MCP that expects users to cURL for a Bearer token with about 32,400 s lifetime, paste it into `PAYPAL_ACCESS_TOKEN`, and re-run cURL when it expires. No built-in refresh. Source: `github.com/paypal/paypal-mcp-server/blob/main/README.md`. Prefer OAuth 2.1 + PKCE with refresh-token rotation (HubSpot) or a first-party key rotation UX (Stripe Restricted Keys). See `mcp/security/*`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Avoid 3: GitHub — silent tool removal without updating `instructions` -->
### Avoid 3: GitHub, silent tool removal without updating `instructions`

`create_pull_request_with_copilot` was removed from the remote surface with no deprecation note in the server `instructions` block; issue #1220 (2025-10-15, closed) shows the resulting user confusion. When removing or gating tools, announce it in the server `instructions` and return structured errors pointing at the replacement. See `mcp/protocol-*`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Avoid 4: Linear — stringified JSON in `content[].text` + noise fields -->
### Avoid 4: Linear, stringified JSON in `content[].text` + noise fields

Linear serializes tool responses as JSON stringified inside a text block (no `structuredContent`) and includes noise fields (`createdAt`, `updatedAt`, `avatarUrl`, `isAdmin`, `isGuest`) in `list_users` even though agents almost only want assignment data. Result: a 17.3k-token tool catalog plus bloated per-call responses. Source: `blog.fiberplane.com/blog/mcp-server-analysis-linear/`. Cross-reference `mcp/responses-*`, `mcp/budget-*`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Avoid 5: Asana V2 — OAuth without DCR and workspace-scoping break -->
### Avoid 5: Asana V2, OAuth without DCR and workspace-scoping break

V2 requires a pre-registered `client_id` + `client_secret` per integrator and does not support Dynamic Client Registration; tokens issued for MCP apps do not work with the REST API. Docker MCP Gateway is blocked on the product decision (`github.com/docker/mcp-gateway/issues/479`) pending the 2026-05-11 V1 sunset (a date that has passed as of 2026-10-20; verify the current status). The vendor called supporting DCR "table-stakes for gateway integrations in 2026".

> Note: prefer Client ID Metadata Documents where the client supports them, keep DCR for clients without them, and never assume either (detect from authorization-server metadata; `mcp/security/*`).

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Avoid 6: PayPal / similar — token-only deploy with no sandbox/prod toggle in the tool surface -->
### Avoid 6: PayPal and similar, token-only deploy with no sandbox/prod toggle in the tool surface

PayPal toggles sandbox/prod with the `PAYPAL_ENVIRONMENT` env var alone. The LLM cannot see which environment it is acting against. Either expose a `whoami`-style tool (Figma does this) or include the environment in every response payload. See `mcp/ops-*`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Avoid 7: Shopify Storefront — zero-auth docs guardrail via prose alone -->
### Avoid 7: Shopify Storefront, zero-auth docs guardrail via prose alone

Shopify Storefront has no authentication and embeds the guardrail "Use only the provided answer for policy responses; don't include external information." in docs rather than in tool descriptions or response envelopes. A compliant agent may obey; a sloppy one will not. When the only enforcement is docs, be explicit about that risk to operators and consider moving the guardrail into the response payload (for example a `policy_enforcement: strict` field the agent is trained to respect). See `decisions/steering-contract.md` for the trust tension.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Avoid 8: Linear — no `structuredContent` *and* catalog eats 17.3k tokens -->
### Avoid 8: Linear, no `structuredContent` and a catalog that eats 17.3k tokens

Not just the JSON-in-text problem (Avoid 4). The full Linear catalog on connect is 17.3k tokens, bumping a session from 61k to 78k before the agent runs its first tool. When catalog token cost exceeds about 5% of the agent's context window, the server should offer a tool-subset selector at connect time (Sentry does this, Supabase does this via URL query params). Linear currently does not.
