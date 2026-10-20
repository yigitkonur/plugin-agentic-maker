---
as_of: 2026-04
verify_before_citing: true
---

# Exemplar servers: cross-cutting observations and which exemplar to study

> Read when: you want the converged and diverged patterns across the 16 vendor servers, a reading order for applying them, which exemplar to copy for your domain, or the questions they leave open.

Overview: `exemplar-servers.md`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#7. Cross-cutting observations -->
## Cross-cutting observations

Five views over the 16 servers: what converged, what diverged, a reading order, an exemplar-by-situation table, and open questions.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#7.1 Which patterns converged across 16 vendors -->
### Patterns that converged across 16 vendors

- **Remote / hosted over stdio.** Every major vendor except PayPal ships a hosted Streamable HTTP endpoint as the primary path. Stdio remains only for local-dev or CI. (Figma and Shopify differ; see Conflicts in `exemplar-servers.md`.)
- **OAuth over long-lived API keys.** Even Stripe, which still accepts API keys, defaults to OAuth for its hosted MCP.
- **Intent-consolidated tools over 1:1 OpenAPI wrappers.** Notion explicitly regretted v1's 1:1 generation; Linear never attempted it; HubSpot, Stripe, and Shopify Storefront started intent-first.
- **`snake_case` as the default identifier convention.** 14 of 16 use it; Atlassian Rovo (`camelCase`) and Notion (`kebab-case`) are the outliers.
- **Streamable HTTP `/mcp` endpoint, deprecating `/sse`.** HubSpot, Cloudflare, Intercom, Notion, Atlassian, Asana V2 all point at Streamable HTTP and mark SSE legacy or reject it outright.
- **Per-request ephemeral sessions.** HubSpot is explicit about it; most hosted servers implement it the same way to scale horizontally.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#7.2 Which patterns diverged -->
### Patterns that diverged

- **Tool count.** 2 (Cloudflare), 4 (Shopify), 6 (Intercom), 14 (Vercel / Zapier Agentic), 15 (Figma), 22 (Notion v2), 23 (Linear), 27 (Supabase), 29 (PayPal), 54 (Atlassian Rovo), 56+ (GitHub).
- **Response shape.** JSON (Stripe, PayPal, Vercel, Intercom, Supabase); stringified JSON in text (Linear); Markdown (Atlassian, Notion); XML (Figma metadata); mixed XML + screenshots (Figma FigJam); untrusted-data-wrapped JSON (Supabase); JS result (Cloudflare Codemode).
- **`structuredContent` adoption.** Spec-recommended. Supabase explicitly opts out. Linear does not use it. Most others ambiguous because their README does not confirm either way.
- **Auth sophistication.** HubSpot (OAuth 2.1 + PKCE + runtime permission intersection) > Atlassian / Linear / Notion / Intercom (OAuth with DCR) > Stripe (OAuth + Restricted Keys) > Asana V2 (OAuth without DCR) > PayPal (manual `client_credentials` then Bearer paste).

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#7.3 Reading order for applying these findings -->
### Reading order for applying these findings

1. Starting a new MCP: read Copy 3 (Cloudflare Codemode) first if your API has more than about 50 endpoints; otherwise read Copy 5 (Linear flattening) and Copy 7 (Intercom universal + direct pair).
2. Hardening an existing MCP: apply Copy 1 and 2 (Supabase annotations + prompt-injection wrapping) and Copy 6 (HubSpot DSL constraints) before anything else.
3. Shipping remote/hosted: apply Disagreement 4 (Streamable HTTP only, per HubSpot) and Copy 4 (URL-query-param config).
4. Tempted to generate tools from OpenAPI: read Avoid 1 (Notion v1 post-mortem) first.
5. For auth: HubSpot > Stripe > PayPal in that order of sophistication. Do not ship PayPal-style manual `client_credentials` in 2026.
6. For enterprise deploy flexibility: combine GitHub's deploy-time description override (Copy 8) with Supabase's URL-query-param config (Copy 4) and GitHub's per-method lockdown (Copy 9).

Copy and Avoid entries: `exemplar-servers-copy-patterns.md`, `exemplar-servers-avoid-patterns.md`, `exemplar-servers-disagreements.md`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#7.4 Which exemplar to study for your domain -->
### Which exemplar to study for your domain

| Your situation | Primary exemplar to copy | Secondary | Why |
|---|---|---|---|
| Large REST API (50+ endpoints) with typed bindings | Cloudflare (Codemode) | Atlassian Rovo (toolset filtering) | Cloudflare's Codemode benchmark is the only published number at this scale. |
| GraphQL backend | Linear | Notion v2 | Linear publicly documents the flattening strategy; Notion v2 shows the post-migration hybrid. |
| Enterprise multi-tenant with scoped permissions | HubSpot | Stripe | HubSpot's OAuth 2.1 + runtime permission intersection is the gold standard; Stripe's Restricted Keys are simpler and work when permissions are static. |
| Narrow task surface (cart, ticket, small workflow) | Shopify Storefront | Intercom | Both prove small tool counts work when the state machine is small. |
| Productivity suite with cross-product entities | Atlassian Rovo | Notion v2 | Rovo's Teamwork Graph shows cross-product walks; Notion's `search` shows a single universal entry. |
| Developer tooling with CLI already present | Vercel | Figma | Vercel's `use_vercel_cli` meta-tool shows the "don't replace the CLI" pattern; Figma bridges IDE and design tool. |
| Platform with 10,000+ potential actions | Zapier | Cloudflare | Zapier's two-mode design is the only public acknowledgement that dynamic meta-tools vs static tools is a user-choice dimension. |
| Observability / incident tooling | Sentry | none | Sentry's tool-group selection at OAuth consent + embedded LLM for NL search are both rare. |
| Billing / financial API | Stripe | none | Stripe's Restricted Keys + Connect account context are the reference implementation. |
| Code forge (git host) | GitHub | Atlassian Rovo Bitbucket | GitHub's enum-dispatcher + lockdown + insiders + description override are all copy-worthy. |

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#7.5 Open questions the exemplars haven't settled -->
### Open questions the exemplars have not settled

- **`structuredContent` in practice.** No exemplar publishes a before/after cost comparison for `structuredContent` vs stringified JSON. Supabase's explicit opt-out suggests the ergonomics story is not settled.
- **DCR adoption.** Asana V2 rejects it; most others accept it. Gateways like Docker MCP Gateway are stuck waiting.
- **Meta-tools vs dedicated tools.** Zapier ships both modes and lets the user choose. No vendor publishes comparative telemetry on which mode wins for which task.
- **Embedded LLM inside the MCP.** Sentry does this (NL search). No other exemplar does. Unclear whether this is a broader pattern or a Sentry-specific workaround.
- **Tool-count ceilings.** Atlassian Rovo 54 and GitHub 56+ work with frontier models today. There is no published evidence on whether mid-tier models degrade gracefully at those counts (`decisions/tool-count.md`).
- **Markdown body format standardization.** Notion ships "Notion-flavored Markdown", Atlassian ships Confluence-flavored Markdown, Figma ships React+Tailwind by default. No convergence on how to serialize rich content for agents.
- **Consent-time tool scoping.** Sentry does it via OAuth consent; Supabase via URL query params; GitHub via toolset flag at deploy. Three different layers for the same problem.
