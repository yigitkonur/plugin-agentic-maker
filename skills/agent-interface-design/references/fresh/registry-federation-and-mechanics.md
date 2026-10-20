---
as_of: unknown
verify_before_citing: true
---

# Registry federation, mirroring, and ecosystem mechanics

> Read when: you stand up an internal MCP registry mirror, federate a catalog, or need the mechanics behind registry namespaces, UUIDs, spec versioning, gateway naming, and the OWASP MCP Top 10 mapping.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#8. Federation, Mirroring, and Self-Hosted Catalogs -->
## Federation, mirroring, and self-hosted catalogs

A key 2025 design choice in the Official Registry was opening the API spec so anyone can implement the registry, not just consume it. Consequences:

- **Internal mirrors:** enterprises can run `ghcr.io/modelcontextprotocol/registry:v1.0.0` inside the VPC, federating from the upstream Official Registry during sync windows. Copilot Enterprise admins can point the organization's MCP registry at a self-hosted instance or Azure API Center; all `github.com/mcp` discovery flows through the mirror.
- **Curated subsets:** a security team can stand up a sub-registry that mirrors only servers passing an internal security review, using the Official Registry UUID as the cross-mirror stable key. When upstream metadata changes but the UUID is stable, automation does not break.
- **Namespace inheritance:** sub-registries that federate inherit the upstream namespace authority. If upstream says `com.stripe/*` is DNS-verified to Stripe, the mirror trusts that assertion; it cannot mint its own `com.stripe/*` entries without overriding authentication.
- **Partner enrichment:** PulseMCP's custom `_meta.com.pulsemcp/server` namespace shows how a federated registry adds value without forking the schema. Any federating registry may attach its own `_meta.<reverse-dns>/*` fields.

Do not confuse self-hosted registries with self-hosted gateways: the registry answers "what is this server?", the gateway answers "execute this call." A private MCP deployment usually needs both: a Docker-hosted Official Registry mirror plus MetaMCP or Portkey for request-path policy.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#9. Ecosystem Mechanics Worth Knowing -->
## Ecosystem mechanics worth knowing

- **DNS-like design:** the Official Registry stores metadata only, never code. It positions itself as the root authority for aggregators, the same split as DNS (names + pointers) vs hosting (content).
- **Opaque stable UUIDs:** each entry has a UUID separate from its name, so aggregators can store cache-safe pointers that survive renames and metadata edits; critical for federation at scale.
- **Namespace authority tiers:** GitHub OAuth, GitHub OIDC, DNS TXT, HTTP `/.well-known/mcp-registry-auth`. The last is the escape hatch for publishers who control a URL but not the domain's DNS.
- **SEP-1400 semver proposal:** authored 2025-08-28 by Anurag Pant and Surbhi Bansal (github.com/modelcontextprotocol/modelcontextprotocol/issues/1400) to replace MCP's date-based versioning with semver 2.0.0. Motivation: batching was added 2025-03-26 and removed 2025-06-18; date-based schemes cannot express non-additive change. Status: open, still debated.
- **Nov 25 2025 spec update:** introduced server identity as first-class, alongside async operations, statelessness, and official extensions.
- **Namespace-collision conventions in the gateway tier:** MetaMCP and MCPJungle both use `{server}__{tool}` (deliberately aligned); Cursor uses `mcp_{server}_{tool_name}`; the OpenAI Agents SDK currently errors on duplicates (openai-agents-python #464, 2025-04-09, still open) rather than de-duping.
- **Glama's 60% mean + 40% minimum server-level weighting** penalizes "one great tool + three sloppy tools" vs a simple average. Reproducible: use the published formula (`registry-community-catalogs.md`) when self-assessing before publishing.
- **Cloudflare API MCP's two-tool compression:** 2,500+ REST endpoints reduced to `search()` + `execute()` in a Dynamic Worker sandbox. Pattern name: Codemode.
- **Klavis white-label OAuth** is unique in the hosted tier: business-branded consent screens for a remote MCP, not a Klavis-branded screen. Useful for vendors embedding MCPs into their own product UX.
- **`workers-oauth-provider`** is a reference implementation for MCP spec 2025-03-26 auth: RFC 7591 DCR + RFC 8414 AS Metadata; the simplest path to a spec-compliant remote MCP.
- **OWASP MCP Top 10 (2025)** exists and maps to the incidents (`registry-trust-incidents.md`): MCP03 (Tool Poisoning / Rug Pull / Schema Poisoning), MCP04 (Supply Chain), MCP09 (Shadow MCP Servers). Defense tactics: `mcp/security/*`.
- **PulseMCP's Sub-Registry API** implements the Generic MCP Registry API specification: anyone can stand up a conforming registry and have MCP clients auto-discover it. Federation is explicit, not accidental.
- **MCPHosting "80% revenue share" pitch** on BrowserMCP/mcp issue #168 (2026-04-03) is the first documented third-party monetization solicitation against a major MCP project. Treat unsolicited "we'll host your server for a revshare" offers as supply-chain risk until they ship a trust model on par with Docker Catalog or Klavis.
