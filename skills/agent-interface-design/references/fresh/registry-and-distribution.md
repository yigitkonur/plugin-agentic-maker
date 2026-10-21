---
as_of: 2026-07-04
verify_before_citing: true
---

# MCP registries, gateways, and hosted services: taxonomy and comparison

> Read when: you decide where to publish an MCP server, which gateway to route consumers through, or how to judge the trust of a third-party MCP, and need the three-tier taxonomy and the platform comparison. Verify before citing.

No overall date is stated; items inside carry their own dates (latest cited: 2026-04-12). Generic meta-server gateway pattern: `mcp/design-*` (composition); hosting substrate: `mcp/ops-*`. This file family covers the distribution and trust layer: catalogs, namespaces, federation, and the named incidents of 2025.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#MCP Registry, Gateway, and Trust Ecosystem | audit-agentic-mcp/references/patterns/registry-and-distribution.md#The Three-Tier Taxonomy -->
## The three-tier taxonomy

The ecosystem splits into three functionally distinct tiers. Confusing them is the most common architectural error in 2025-26.

| Tier | What it does | What it is NOT | Examples |
|---|---|---|---|
| **Registries** | Index metadata about servers; answer "does this server exist?" and "who owns this name?" | A runtime; does not execute tool calls | Official Registry, Smithery (hybrid), MCP.so, PulseMCP, Docker MCP Catalog, GitHub MCP Registry, Glama |
| **Gateways / Aggregators** | Sit on the request path; aggregate N upstream servers into 1 endpoint; apply policy, auth, logging | A catalog; they consume registries, not replace them | MetaMCP, MCPJungle, Portkey MCP Gateway, Cloudflare AI Gateway, Glama Gateway |
| **Hosted Tool-as-a-Service** | Execute tools on their infra with managed OAuth; you build against their API, not MCP directly | A neutral registry; they are the runtime and the catalog | Composio, Klavis, Arcade.dev, Pica, Smithery (hybrid), Gumloop, Superinterface |

**The consolidation event:** Anthropic donated MCP to the Linux Foundation Agentic AI Foundation on 2025-12-09 (anthropic.com, 2025-12). The Official MCP Registry preview launched 2025-09-08 (blog.modelcontextprotocol.io, 2025-09) and froze API v0.1 around 2025-10-24. GitHub, Docker, PulseMCP, and Smithery all now either federate from it or implement its API. v0 is unstable: do not implement it (docs.github.com, 2025-10).

Per-tier files: `registry-official-github-docker.md` and `registry-community-catalogs.md` (registries), `registry-gateways.md`, `registry-hosted-services.md`.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#4. Comparison Table -->
## Comparison table

| Platform | Tier | Trust | Manifest | Versioning | Namespace | Pricing | Audience |
|---|---|---|---|---|---|---|---|
| Official Registry | Registry | GitHub OAuth + DNS/HTTP + OIDC | `server.json` | Opaque UUID + semver; API v0.1 | Reverse-DNS `io.github.*/*`, `com.example/*` | Free | Sub-registries, aggregators |
| Smithery | Registry + Hosted | Verified badge + server-card scan | `smithery.yaml` + `/.well-known/mcp/server-card.json` | `serverInfo.version` | `@org/server` | Free publish; paid hosting | MCP builders + agent devs |
| MCP.so | Registry | **None** | none | none | GitHub-issue curated | Free | Community |
| PulseMCP | Registry | Curated + vendor audits | Extended `server.json` | Sub-Registry API v0.1 | Inherits official | Free + partner API paid | Partners, analysts |
| OpenTools | Registry + Gateway | Managed connectors | `ref` in completions | none | Flat `ref` | Token pass-through + execution | LLM app builders |
| Docker Catalog | Registry | **Signatures + SBOM + provenance + container isolation** | OCI reference | OCI tags | Docker Hub `mcp/*` | Free | Mainstream devs |
| GitHub Registry | Registry | Curated; Azure API Center for enterprise | v0.1 spec | v0.1 API | Inherits official | Free + Azure Standard tier | Copilot customers |
| Glama | Registry + Gateway | **Quantitative quality score** | `glama.json` | Server releases | GitHub `owner/repo` | Free + paid | Authors + consumers |
| MetaMCP | Gateway | Better Auth + OIDC + multi-tenant scopes | Namespace groups | none | `{Server}__{tool}` prefix | Free OSS | Self-host teams |
| MCPJungle | Gateway | Static bearer; OAuth upstream soon | JSON or CLI | none | `{server}__{tool}` | Free OSS | Private agents |
| Portkey | Gateway | OAuth 2.1 + IdP + RBAC | `mcpServers` + Bearer | none | `{slug}` in URL | Unpublished | 3,000+ GenAI teams |
| Cloudflare | Gateway + Hosted | Access OAuth + Gateway policy + DCR | `mcpServers` JSON | Protocol version | Product subdomains | AI Gateway on all plans | Enterprise |
| Composio | Hosted | SOC 2 + ISO 27001 + VPC | N/A | API-stable | Per-toolkit | Free 20K, $29, $229, custom | Agent SaaS builders |
| Klavis | Hosted | SOC 2 Type II + GDPR + zero-trust | N/A | Python SDK v2.20.0 | Progressive (Strata) | Free OSS + paid cloud | AI labs + production |
| Arcade.dev | Hosted | User-scoped + SSO/SAML | `@app.tool` | Not documented | `Provider.Capability` | Free, $25, custom | Dev teams + enterprise |
| Pica | Hosted | Secret header | N/A | none | none | Unknown | OpenAI Agent Builder |
| MCP-Hub Verified | Trust overlay | Incorporation + tax ID + domain + security audit | N/A | none | Cross-registry | $199/yr | Publishers needing a visible badge |

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#When This File Applies -->
## When to open which file

- "Where should we publish our MCP server?" -> `registry-publisher-picker.md`.
- "How do we prevent brand squatting on our MCP?" -> `registry-trust-incidents.md` (postmark-mcp), `registry-publisher-picker.md` (tool vendor), `registry-publish-how-tos.md` (Official Registry with DNS).
- "Our enterprise wants a private catalog" -> `registry-official-github-docker.md` (GitHub + Azure API Center, self-host Official Registry), `registry-gateways.md` (MetaMCP, Portkey).
- "We want one endpoint for many servers" -> `mcp/design-*` for the pattern; `registry-gateways.md` for products.
- "How do we know a third-party MCP is trustworthy before we install it?" -> `registry-community-catalogs.md` (Glama quality score), `registry-official-github-docker.md` (Docker signing), `registry-trust-incidents.md`.
- "Can we just build against Composio / Klavis / Arcade instead of MCP directly?" -> `registry-hosted-services.md`: yes, with the trade-off that you are no longer publishing to the MCP ecosystem; you consume a hosted runtime whose tools happen to include MCP.
- Federation, mirroring, namespace mechanics -> `registry-federation-and-mechanics.md`.
