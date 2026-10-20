---
as_of: 2026-04
verify_before_citing: true
---

# Exemplar profiles: GitHub, Cloudflare, Vercel

> Read when: you design a developer-platform MCP server (code forge, large REST API, CLI-adjacent) and want the exact choices GitHub, Cloudflare, and Vercel made. Overview and comparison: `exemplar-servers.md`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#GitHub — `github/github-mcp-server` -->
## GitHub (`github/github-mcp-server`)

- **Source:** `github.com/github/github-mcp-server`, preview 2025-04-04.
- **Surface:** 56+ tools grouped by toolsets (`actions`, `issues`, `pull_requests`, `repos`, `code_security`, `dependabot`, `discussions`, `gists`, `notifications`, `orgs`, `projects`, `secret_protection`, `security_advisories`, `users`, `copilot`). Dynamic toolset discovery.
- **Naming:** `snake_case`, resource-prefixed.
- **Granularity:** hybrid. Action-enum dispatchers for high-cardinality domains (`issue_read`, `issue_write`, `pull_request_read` taking a `method` arg), one-per-operation for the rest. A deliberate middle path between "verb per endpoint" (PayPal) and "2 tools total" (Cloudflare).
- **Unique:**
  - Description override at deploy time via `github-mcp-server-config.json`: operators rewrite tool descriptions for their environment without forking.
  - Insiders channel via `/insiders` URL suffix or `X-MCP-Insiders: true` header: two activation vectors for the same flag.
  - Lockdown mode filters response content per method when the caller lacks push access, finer than a binary read-only flag.
  - Dynamic tool discovery (beta, local only) gates heavy toolsets behind an initial discovery step.
  - Read-only mode as a first-class deploy flag.
- **Auth / transport:** OAuth (GitHub App/OAuth App) or PAT Bearer locally; OAuth remote. GHES supports PAT + OAuth. Remote at `api.githubcopilot.com/mcp/`, local stdio, Docker, GHE Cloud with data residency via `ghe.com`. No remote endpoint for GHES.
- **Most interesting tool:** `github_support_docs_search`. The parameter description is itself a behavioral policy: "Input from the user about the question they need answered. This is the latest raw unedited user message. You should ALWAYS leave the user message as it is, you should never modify it." Description-as-enforcement.
- **Known issue:** `create_pull_request_with_copilot` silently removed from remote (issue #1220, 2025-10-15, closed); see Avoid 3 in `exemplar-servers-avoid-patterns.md`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Cloudflare — `mcp-server-cloudflare` + product servers -->
## Cloudflare (`mcp-server-cloudflare` and product servers)

- **Source:** `github.com/cloudflare/mcp-server-cloudflare`; `developers.cloudflare.com/agents/model-context-protocol/mcp-servers-for-cloudflare/`; `blog.cloudflare.com/model-context-protocol/` (2024-12-20, the earliest public MCP implementation from a major vendor).
- **Surface:** 2 tools total for the Cloudflare API MCP: `search()` and `execute()`. Plus 16+ product-specific servers (docs, bindings, builds, observability, radar, containers, browser rendering, logpush, AI Gateway, AI Search, audit logs, DNS analytics, DEX, CASB, GraphQL, Agents SDK), each at its own URL with its own tools.
- **Codemode pattern:** `execute()` accepts JavaScript written against the typed OpenAPI spec, runs it in an isolated Dynamic Worker sandbox. The agent composes, Cloudflare runs.
- **Published benchmark:** 2,594 endpoints x full schemas = about 1,170,000 tokens for native MCP exposure. Required-params-only = 244,000. Codemode = about 1,000 tokens. The most concrete large-surface cost number publicly available as of 2026.
- **JSDoc-typed methods:** the API surface exposes `camelCase` JS methods with JSDoc types; agents write idiomatic JS against them.
- **Auth / transport:** OAuth or API token. Streamable HTTP `/mcp`; deprecated `/sse`.
- **Implication:** the right abstraction for large APIs is a sandboxed runtime, not a flat tool list. Only relevant if your API has typed bindings the agent can call; not applicable to event-driven or stateful APIs.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Vercel MCP -->
## Vercel MCP

- **Source:** `vercel.com/docs/agent-resources/vercel-mcp/tools`.
- **Surface:** exactly 14 tools, `snake_case`: `search_documentation`, `list_teams`, `list_projects`, `get_project`, `list_deployments`, `get_deployment`, `get_deployment_build_logs`, `get_runtime_logs`, `check_domain_availability_and_price`, `buy_domain`, `get_access_to_vercel_url`, `web_fetch_vercel_url`, `use_vercel_cli`, `deploy_to_vercel`.
- **Unique:**
  - `use_vercel_cli`: "Instructs the LLM to use Vercel CLI commands with --help flag for information." A meta-tool that does not execute; it nudges the agent to run the CLI. Counter-example to "everything must be a tool call" (`decisions/mcp-vs-cli-evidence.md`).
  - `get_access_to_vercel_url` creates a temporary shareable link for protected deployments: the MCP acts as an auth bridge for previews.
  - `web_fetch_vercel_url` pairs with the access tool so agents can fetch behind-auth preview content without separate credential plumbing.
