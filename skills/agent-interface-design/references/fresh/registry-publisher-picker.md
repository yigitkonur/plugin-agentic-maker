---
as_of: unknown
verify_before_citing: true
---

# Publisher picker: which registries and gateways for which archetype

> Read when: you decide where to publish (or whether to publish at all) an MCP server, matching an archetype (hobby, indie SaaS, enterprise internal, community OSS, tool vendor, platform builder) to registries and gateways.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#6. Publisher Picker Rubric -->
## Publisher picker rubric

Match archetype to registries and gateways. Do not publish everywhere reflexively: every surface is another place your namespace can drift, another scan that can fail, another badge to re-earn.

| Archetype | Primary | Secondary | Why |
|---|---|---|---|
| **Personal / hobby OSS server** | Official Registry (`io.github.<you>/*` via GitHub OAuth) | PulseMCP + Glama auto-index | GitHub OAuth is the cheapest trust foundation: zero-cost verified identity. |
| **Indie SaaS selling the MCP** | Smithery (distribution + analytics + managed OAuth) | Official Registry with `com.<domain>/*` + Docker Catalog | Smithery handles OAuth and provides user analytics; DNS-verified namespace protects brand; Docker Catalog gets you into `mcp/*` with signatures. |
| **Enterprise internal MCP** | Self-hosted MetaMCP **or** Portkey + GitHub MCP Registry via Azure API Center | Cloudflare Access for OAuth; MCP-Hub Verified ($199/yr) if you need an external green badge | Internal registry with RBAC, audit logs, IdP integration. **Never publish internal servers to public registries**: leakage risk is higher than discoverability upside. |
| **Open-source community server wanting trust signals** | Docker MCP Catalog (signed images + SBOM) | Glama (public quality score) + Official Registry | Docker signing is the strongest technical trust signal; Glama provides a reproducible quality ranking for consumers. |
| **Tool vendor (Stripe/Postmark class)** | Official Registry with DNS-verified `com.yourbrand/*` + Smithery + Docker Catalog + GitHub Registry | Composio/Klavis/Arcade for managed tool hosting if you don't want to operate the runtime | Brand protection via DNS-verified namespace + distribution across every client-facing catalog. **The `postmark-mcp` incident proves brand squatting is active: claim your namespace now.** |
| **Agent platform builder (consuming only)** | Gateway (MetaMCP / Portkey / Cloudflare) | Hosted (Composio / Klavis / Arcade) per OAuth workload | Do not publish. Aggregate upstream behind one controlled endpoint with observability; shift OAuth complexity to a hosted provider only when you need it. |

**Never rely solely on** MCP.so (no verification), Pica (single-tenant secret header), or any registry with no namespace authentication, for brand-sensitive work.

Context: incidents in `registry-trust-incidents.md`; commands in `registry-publish-how-tos.md`.
