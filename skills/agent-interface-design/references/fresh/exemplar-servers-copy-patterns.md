---
as_of: 2026-04
verify_before_citing: true
---

# Exemplar patterns worth copying (Copy 1 to 13)

> Read when: you want a production-validated pattern with its source vendor for a design call (annotations, injection wrapping, Codemode, URL config, flat filters, restricted DSL, search/fetch pairs, description override, lockdown, introspection, consent-time scoping, ephemeral sessions, graph tools).

Overview and profiles: `exemplar-servers.md`. Principles these validate: `mcp/design-*`, `mcp/schemas-*`, `mcp/responses-*`, `mcp/security/*`, `mcp/ops-*`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#3. Copy-this patterns -->
## Copy-this patterns

Thirteen patterns, each tied to a vendor and source.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Copy 1: Supabase — tool annotations + input AND output Zod schemas on every tool -->
### Copy 1: Supabase, tool annotations + input AND output Zod schemas on every tool

Supabase declares `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint` on every tool, alongside Zod `parameters` and `outputSchema`. Clients can precompute which tools need consent gating and which are safe for batch execution. Source: `packages/mcp-server-supabase/src/tools/database-operation-tools.ts` (GitHub, 2025). Pair with `mcp/schemas-*` and `decisions/steering-contract.md`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Copy 2: Supabase — prompt-injection wrapping of untrusted tool output -->
### Copy 2: Supabase, prompt-injection wrapping of untrusted tool output

`execute_sql` wraps returned rows in `<untrusted-data-${UUID}>...</untrusted-data-${UUID}>`, where the UUID is freshly generated per call, plus an embedded instruction telling the agent to ignore any commands inside. Defends against SQL result rows that contain injected prompts. Same source file. Cross-reference `mcp/security/*`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Copy 3: Cloudflare — Codemode for large API surfaces -->
### Copy 3: Cloudflare, Codemode for large API surfaces

For a 2,594-endpoint API, Cloudflare published 1,170,000 tokens native to about 1,000 tokens via Codemode (`search()` + `execute()`), running typed JS against the OpenAPI spec in a Dynamic Worker sandbox. Source: `developers.cloudflare.com/agents/model-context-protocol/mcp-servers-for-cloudflare/`. Use this when the API has more than about 50 endpoints. Cross-reference `mcp/design-*`, `mcp/budget-*`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Copy 4: Supabase — URL-query-param server configuration -->
### Copy 4: Supabase, URL-query-param server configuration

`mcp.supabase.com/mcp?project_ref=...&read_only=true&features=database,docs` reconfigures the tool surface without restarting the MCP client. Adopt for any multi-tenant hosted MCP. See `mcp/ops-*`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Copy 5: Linear — flatten nested filters + inline-enum descriptions -->
### Copy 5: Linear, flatten nested filters + inline-enum descriptions

Linear collapses GraphQL's nested filter objects into flat `assigneeId`, `teamId`, `stateId` and documents enum values inside the description string, for example `"Priority: 0 = No priority, 1 = Urgent, 2 = High, 3 = Normal, 4 = Low"`. Source: `blog.fiberplane.com/blog/mcp-server-analysis-linear/` (2025). Cross-reference `mcp/schemas-*`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Copy 6: HubSpot — restricted query DSL for LLM reliability -->
### Copy 6: HubSpot, restricted query DSL for LLM reliability

Single-string `key:value` tokens: `object_type:contacts associated_companies:12345 limit:100 sort:lastmodifieddate:desc`. Explicitly bans boolean OR, nested expressions, and relative dates because LLMs get them wrong. Source: `product.hubspot.com/blog/unlocking-deep-research-crm-connector-for-chatgpt` (2025-06-18). Cross-reference `fresh/model-behavior.md`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Copy 7: Intercom — universal `search`/`fetch` + direct-tool pair -->
### Copy 7: Intercom, universal `search`/`fetch` + direct-tool pair

Pair a DSL-driven `search`/`fetch` pair for Deep-Research-style broad browsing with direct per-resource tools (`search_conversations`, `get_conversation`) for precise filters. Agents that know the domain pick the direct tool; agents exploring pick the universal pair. Source: `developers.intercom.com/docs/guides/mcp`. See `mcp/design-*`, `mcp/budget-*`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Copy 8: GitHub — description override at deploy time -->
### Copy 8: GitHub, description override at deploy time

`github-mcp-server-config.json` lets operators rewrite tool descriptions without forking. Ship this any time enterprises will tune tool behavior per environment (for example "in this org, `issue_write` is read-only"). Source: `github.com/github/github-mcp-server`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Copy 9: GitHub — lockdown mode filters response content per method -->
### Copy 9: GitHub, lockdown mode filters response content per method

When the author lacks push access, lockdown filters the response of specific methods (not just hides the whole tool). More granular than a binary read-only flag. Source: `github.com/github/github-mcp-server`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Copy 10: Figma — server-side repo introspection via `create_design_system_rules` -->
### Copy 10: Figma, server-side repo introspection via `create_design_system_rules`

Scans the caller's codebase from the MCP server side and emits a rules file the agent can consume. Inverts the usual "agent reads repo" flow: the MCP knows its own domain better and packages that knowledge for the calling agent. Source: `developers.figma.com/docs/figma-mcp-server/tools-and-prompts/`. See `mcp/budget-*`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Copy 11: Sentry — tool-group selection at OAuth consent -->
### Copy 11: Sentry, tool-group selection at OAuth consent

The user picks which tool groups (Issues / Errors / Projects / Seer) are exposed during the OAuth consent flow, shrinking the post-connect tool catalog per user rather than per tenant. Source: `docs.sentry.io/ai/mcp/`. See `mcp/security/*`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Copy 12: HubSpot — ephemeral per-request sessions -->
### Copy 12: HubSpot, ephemeral per-request sessions

No server-side session state. Each HTTP request re-runs auth, permission intersection, and execution. Scales horizontally, fails safe (a crashed worker does not lose session state), pairs with OAuth 2.1 refresh-token rotation. Source: `product.hubspot.com/blog/unlocking-deep-research-crm-connector-for-chatgpt` (2025-06-18). See `mcp/ops-*`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Copy 13: Atlassian Rovo — cross-product Teamwork Graph tools -->
### Copy 13: Atlassian Rovo, cross-product Teamwork Graph tools

`getTeamworkGraphContext` and `getTeamworkGraphObject` (beta) return entity context that spans Jira + Confluence + Bitbucket for a single object. When your product has multiple surfaces referring to the same entity, expose the graph walk instead of forcing the agent to join three tool calls. Source: `support.atlassian.com/atlassian-rovo-mcp-server/docs/supported-tools/`.
