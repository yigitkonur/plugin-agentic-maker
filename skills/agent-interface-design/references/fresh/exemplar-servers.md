---
as_of: 2026-04
verify_before_citing: true
---

# Exemplar MCP servers: survey overview, comparison, conflicts

> Read when: you need evidence of which tradeoffs 16 production vendor MCP servers chose (tool count, naming, auth, transport, response shape) before making a design call. Verify before citing; vendors redesign fast.

Empirical survey of 16 production MCP servers shipped by major SaaS vendors in 2025-26. The principle files (`mcp/design-*`, `mcp/schemas-*`, `mcp/responses-*`, `mcp/security/*`, `mcp/ops-*`, `mcp/budget-*`) describe principles; this file family records which vendors chose which tradeoff.

**Headline findings, 2026-04.** The ecosystem has converged on remote/hosted transports over stdio, OAuth 2.1 + PKCE over long-lived API keys, and intent-consolidated tools over 1:1 OpenAPI wrappers. It has diverged sharply on tool-count philosophy (Cloudflare 2, GitHub 56, Atlassian Rovo 54) and on `structuredContent` adoption (spec-recommended, but Supabase and Linear opt out in favor of JSON-in-text).

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Exemplar MCP Server Analysis | audit-agentic-mcp/references/patterns/exemplar-servers.md#1. Per-server profiles -->
## Where the profiles are

- GitHub, Cloudflare, Vercel: `exemplar-servers-developer-platforms.md`
- Sentry, Supabase, Figma: `exemplar-servers-observability-and-design.md`
- Linear, Notion, Atlassian Rovo, Asana V2: `exemplar-servers-work-management.md`
- Stripe, PayPal, Shopify Storefront: `exemplar-servers-payments-and-commerce.md`
- HubSpot, Intercom, Zapier: `exemplar-servers-crm-and-automation.md`
- Patterns to copy and avoid: `exemplar-servers-copy-patterns.md`, `exemplar-servers-avoid-patterns.md`
- Design disagreements and one-offs: `exemplar-servers-disagreements.md`; cross-cutting findings and exemplar-by-situation table: `exemplar-servers-synthesis.md`

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#2. Head-to-head comparison -->
## Head-to-head comparison

| Server | Tools | Naming | Granularity | Schema | Response | Auth | Transport | `outputSchema` + `structuredContent` |
|---|---|---|---|---|---|---|---|---|
| GitHub | 56+ | `snake_case` + enum verbs | Hybrid: enum dispatchers for high-cardinality | Flat; override via config file | Text, some JSON | OAuth / PAT Bearer | Streamable HTTP | No |
| Linear | 23 | `snake_case` | Intent-consolidated | Flat | Stringified JSON in text | OAuth | Streamable HTTP | No |
| Stripe | ~25 | `snake_case` | Intent-consolidated | Flat | JSON | OAuth / Restricted API Key | Streamable HTTP | n/a |
| Notion | 22 (v2) | `kebab-case` | Hybrid: AI-first + API wrappers | Zod from OpenAPI | Notion-flavored Markdown | OAuth | Streamable HTTP + SSE | n/a |
| Sentry | ~10-15 | `snake_case` | Intent + embedded LLM | Flat | Text | OAuth / Token | Streamable HTTP + stdio | n/a |
| Figma | 15 | `snake_case` | Per-capability | Flat | Text / XML / React+TW / screenshots | Desktop app session | Local stdio, remote | n/a |
| Atlassian Rovo | 54 | **`camelCase`** + dotted sub-actions | Hybrid: flat + nested | Flat | Markdown for pages | OAuth | Streamable HTTP | n/a |
| Cloudflare API | 2 | `camelCase` in JS code | Codemode (JS sandbox) | JS runs against OpenAPI | JS result | OAuth / API token | Streamable HTTP | n/a |
| PayPal | 29 | `snake_case` | One-per-operation | Flat | JSON | OAuth `client_credentials` then Bearer | stdio / npx | n/a |
| Shopify Storefront | 4 | `snake_case` | Workflow-consolidated | JSON-RPC 2.0 | JSON | **None** | HTTP | n/a |
| Asana V2 | `tools/list` | n/a | n/a | n/a | n/a | OAuth (no DCR) | Streamable HTTP | n/a |
| Supabase | 27 | `snake_case` | Feature-grouped | **Zod v4 in + out** | JSON + `<untrusted-data-UUID>` wrapping | OAuth / PAT | Streamable HTTP | **`outputSchema` yes, `structuredContent` NO (explicit)** |
| HubSpot | auto-discovered | n/a | Per-RPC via `@ChirpTool` | Zod | JSON | **OAuth 2.1 + PKCE** | Streamable HTTP (custom impl) | n/a |
| Vercel | 14 | `snake_case` | Flat per-operation | Flat | JSON | OAuth | Streamable HTTP | n/a |
| Intercom | 6 | `snake_case` | Universal (`search`/`fetch`) + direct | Flat + DSL | JSON with pagination | OAuth / Bearer | Streamable HTTP | n/a |
| Zapier Agentic | 14 meta | `snake_case` | Dynamic action discovery | Flat | JSON | API key / OAuth | Streamable HTTP | n/a |

## Conflicts

| Item | Claim 1 | Claim 2 |
|---|---|---|
| Cloudflare product servers | Here and in the profile: 16+ product servers | `registry-gateways.md`: 10+ product servers |
| Hosted transport | Synthesis: every major vendor except PayPal ships a hosted Streamable HTTP endpoint | Figma is local stdio with remote tools mixed in; Shopify is plain HTTP |
| Atlassian Rovo tool count | Headline 54 (used throughout) | Components listed sum to 69: Jira 13, Confluence 11, JSM 4, Bitbucket Cloud 23, Rovo code/shared 4, Teamwork Graph 2, Compass 12 |
| Figma tool count | 15 tools | 16 tool names listed in the profile |
| Supabase schema | `outputSchema` on every tool | README: `structuredContent` is not sent |
| HubSpot SSE quote | "SSE requires long-lived connections, harder for load balancers in auto-scaling environments" | "Supporting SSE would have introduced load balancer and scaling complexity" (same blog, cited in two places) |

> Unresolved: Atlassian 54 vs 69 and Figma 15 vs 16 cannot be settled from the source; re-count against the vendor's current tool page. The other rows are different readings of one source and are kept as written.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#7.6 How this file relates to its siblings -->
## How this file relates to its siblings

- **Principles:** the `mcp/` files (design, schemas, responses, security, ops, budget).
- **Evidence:** this file family. When a principle file recommends a pattern, look here for which vendor validated it in production and how.
- **Counter-examples:** `exemplar-servers-avoid-patterns.md`. When a principle has public failure data (Notion v1, PayPal auth), it is cited there.
- **Disagreements:** `exemplar-servers-disagreements.md`. Where principle files present something as settled but exemplars disagree, the disagreement is recorded so you can pick deliberately.
- **Dates:** every claim citing a doc, blog, or repo includes the YYYY-MM-DD (or YYYY-MM) it was published or observed. Recompute staleness when reusing: exemplars older than 6 months may have shipped redesigns.
- **Re-cite, do not paraphrase.** When you pull a claim into a design doc or PR, keep the vendor attribution and the date. Unattributed exemplar claims age poorly.
