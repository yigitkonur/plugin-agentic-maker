---
as_of: 2026-04
verify_before_citing: true
---

# Exemplar profiles: HubSpot, Intercom, Zapier

> Read when: you design an MCP server for a CRM, support, or automation platform: OAuth 2.1 with per-call permission intersection, a restricted query DSL, universal-plus-direct tool pairs, or a classic-vs-agentic dual mode. Overview: `exemplar-servers.md`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#HubSpot Remote MCP -->
## HubSpot Remote MCP

- **Source:** `developers.hubspot.com/mcp`; engineering blog `product.hubspot.com/blog/unlocking-deep-research-crm-connector-for-chatgpt` (2025-06-18). GA 2026-04-13.
- **Auth:** OAuth 2.1 + PKCE required, one of very few vendors explicit about 2.1. Refresh token rotation mandatory. The server intersects OAuth app scopes with live user permissions on every call (adds a few dozen ms).
- **Transport:** Streamable HTTP, explicitly rejects SSE. Blog: "SSE requires long-lived connections, harder for load balancers in auto-scaling environments." Because the Java MCP SDK did not yet support Streamable HTTP at build time, HubSpot wrote a custom transport inside the SDK and committed to contribute it back upstream.
- **Tool surface:** an internal MCP Gateway auto-discovers RPC methods annotated `@ChirpTool` across microservices and auto-registers them as MCP tools: a service-catalog-driven tool surface. New tools appear as soon as a team ships an annotated RPC.
- **Session model:** ephemeral session per HTTP request; no state retained server-side. Pairs naturally with permission intersection on every call.
- **Query DSL:** single-string token-based, for example `object_type:contacts associated_companies:12345 limit:100 sort:lastmodifieddate:desc`. No boolean OR, no nested expressions, no relative dates: dropped intentionally because LLMs get them wrong (Copy 6).
- **Safety posture:** read-only scopes + no sensitive properties by default. The intersection layer means even if an OAuth app grants more than the user has, runtime narrows to the user.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Intercom — `mcp.intercom.com` -->
## Intercom (`mcp.intercom.com`)

- **Source:** `developers.intercom.com/docs/guides/mcp`.
- **Surface:** 6 tools: universal `search`, `fetch`, plus direct `search_conversations`, `get_conversation`, `search_contacts`, `get_contact`.
- **Pattern:** explicit universal + direct pair. `search` takes a DSL (`object_type:conversations`); `fetch` retrieves a specific resource; direct tools offer richer filters (Copy 7).
- **Response:** pagination with `total_in_page`, `results`, `pages`, `_note`, cursor via `starting_after`. Up to 150 items/page.
- **Auth / transport:** OAuth (recommended, browser) or Bearer. Streamable HTTP `/mcp`; SSE `/sse` deprecated but retained.
- **Status:** US workspaces only, 2026-04.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Zapier — `zapier/zapier-mcp` -->
## Zapier (`zapier/zapier-mcp`)

- **Source:** `github.com/zapier/zapier-mcp`.
- **Two-mode surface** (unique across exemplars):
  - **Classic mode:** the user enables specific actions; each enabled action becomes a dedicated tool with typed parameters (for example `gmail_send_email` with `to/subject/body`). Shaped like the user's workflow.
  - **Agentic mode (beta):** 14 static meta-tools discover/enable/disable/execute actions dynamically. Shaped like a platform API.
- **Rationale:** users pick a "focused handful" (Classic) when the workflow is known, or "broad across the stack" (Agentic) when the agent must explore. Exposes 8,000+ apps and 40,000+ actions.
- **Auth:** API key (personal) or OAuth (multi-user).
- **Implication:** Zapier is the only exemplar to publicly concede that one surface does not fit both modes of use; everyone else picks one and defends it.
