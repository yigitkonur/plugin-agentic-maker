---
as_of: unknown
verify_before_citing: true
---

# Hosted tool-as-a-service: Composio, Klavis, Arcade.dev, Pica, Gumloop, Superinterface

> Read when: you consider building against a hosted runtime with managed OAuth instead of publishing an MCP server, and need compliance, user-scoping, white-labeling, and pricing differences. Prices are as of 2025; verify before citing.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#3. Hosted Tool-as-a-Service — the Runtime Tier -->
## The runtime tier

You build against their API, not MCP directly. They take on OAuth, token refresh, compliance, rate limiting.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#Composio -->
## Composio

"Your agent decides what to do. We handle the rest." 1,000+ managed app integrations, JIT tool calls with scoped permissions, centralized auth with token refresh. SOC 2 + ISO 27001:2022, ephemeral sandboxes, optional VPC/BYOC enterprise tier.

**Pricing** (composio.dev/pricing, 2025): Free 20K calls/mo; Starter $29/mo for 200K + $0.299 / 1K overage; Business $229/mo for 2M + $0.249 / 1K overage; Enterprise custom + SOC 2 + VPC.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#Klavis -->
## Klavis

Hosted MCP + open-source SDK. Markets itself as an RL/training environment: live environments for training and running agents with progressive tool discovery.

- **Trust:** SOC 2 Type II + GDPR; zero-trust architecture; multi-tenant isolation; per-tenant throttling; RBAC + guardrails; advertised 99.99% uptime SLA.
- **Namespace:** `Klavis-AI/klavis` GitHub org; REST at `api.klavis.ai/v1/mcp-server/strata` and `/instance`.
- **Distinctive feature:** white-label OAuth: business-branded OAuth consent screens (logo, colors, text). Unique among hosted-MCP vendors.
- **Deployment modes:** cloud (`klavis.ai`), self-host via Docker `ghcr.io/klavis-ai/github-mcp-server:latest`, or pipx `strata-mcp`.
- **"Strata" progressive discovery:** servers, categories, actions, schemas (klavis.ai/blog, 2025).

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#Arcade.dev -->
## Arcade.dev

MCP runtime, SDK, hosted cloud, plus on-prem, VPC, and air-gapped deployment. `@app.tool` Python decorators; `arcade configure` to deploy.

- **Trust:** user-scoped auth (not service accounts); IDP flows; dedicated-tenant isolation; RBAC; SSO/SAML on enterprise; OSS MIT-licensed SDK.
- **Namespace:** `Provider.Capability` (for example `Google.SendEmail`).
- **Pricing** (arcade.dev/pricing, 2025): Hobby FREE (1,000 standard executions, 100 user challenges, 50 pro executions, 1 Arcade-hosted worker, 5 self-hosted); Growth $25/mo + usage (2,000 std at $0.01 after, 600 challenges at $0.05 after, $0.05/server-hour); Enterprise custom.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#Pica -->
## Pica

Hosted MCP connector. Single endpoint `https://mcp.picaos.com/mcp`. Custom header `x-pica-secret: YOUR_SECRET_KEY`; no OAuth documented (mcp.picaos.com, 2025). Pitched for OpenAI Agent Builder. Secret-header auth is weaker than the rest of this tier; fine for prototypes, avoid for regulated data.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#Gumloop and Superinterface (honorable mentions) -->
## Gumloop and Superinterface (honorable mentions)

**Gumloop** (gumloop.com/mcp, 2025): workflow-oriented hosted MCP where each "flow" is exposed as a tool; useful when the MCP audience is non-technical operators composing flows visually rather than code.

**Superinterface** (superinterface.ai, 2025): hosted MCP for embedding AI assistants into customer-facing apps; overlaps with Klavis's white-label approach but positioned toward end-user chat rather than agent workloads.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#Hosted-tier decision factors -->
## Hosted-tier decision factors

| Factor | Composio | Klavis | Arcade | Pica |
|---|---|---|---|---|
| Compliance ceiling | SOC 2 + ISO 27001 + VPC | SOC 2 Type II + GDPR | SSO/SAML + dedicated tenant | Secret header only |
| User-scoped auth | Per-connection | Strata progressive | **Yes (first-class)** | No (shared secret) |
| White-label | Enterprise only | **Branded OAuth screens** | Via on-prem | No |
| Self-host | No | Yes (Docker, pipx) | Yes (OSS MIT SDK) | No |
| Published pricing | Yes, 4 tiers | OSS + cloud (paid tiers) | Yes, 3 tiers | Not published |
| Best fit | Agent SaaS with 1,000+ integrations target | Training envs + white-label consumer products | Teams that need user-scoped auth with full audit | Quick prototypes against OpenAI Agent Builder |
