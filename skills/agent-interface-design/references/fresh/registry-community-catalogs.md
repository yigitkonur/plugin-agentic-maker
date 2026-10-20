---
as_of: unknown
verify_before_citing: true
---

# Registries: Smithery, MCP.so, PulseMCP, Glama, OpenTools, MCP-Hub

> Read when: you consider publishing to or trusting a community or commercial MCP catalog and need its trust model, manifest, scoring formula, and gates. Verify before citing.

Official, GitHub and Docker catalogs: `registry-official-github-docker.md`.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#Smithery.ai — Registry + Hosted Gateway + CLI -->
## Smithery.ai (registry + hosted gateway + CLI)

Self-styled largest open MCP marketplace. Hybrid: catalog + managed hosting + OAuth broker + CLI.

- **Trust model:** "Verified" badge after publishing; automated scan on publish via `/.well-known/mcp/server-card.json`; crawls from Cloudflare Workers IPs with `User-Agent: SmitheryBot/1.0`; servers must return HTTP 401 (not 403) for unauthenticated requests so OAuth discovery works per RFC 9728 (smithery.ai/docs/build, 2025). Tokens advertised as "ephemeral."
- **Manifest:** `smithery.yaml` at build time (`startCommand`, `type: stdio|sse`, `configSchema`, `commandFunction`) plus runtime `/.well-known/mcp/server-card.json` (github.com/smithery-ai/cli, 2026-04-12, v4.8.0).
- **Versioning:** `serverInfo.version` per deploy.
- **Namespace:** `@org/server` (for example `-n @your-org/your-server`).
- **Pricing:** free publish; paid managed hosting tiers.
- **Audience:** MCP server builders who want analytics + hosted OAuth; agent devs who want one-click `smithery mcp add`.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#MCP.so -->
## MCP.so

Community directory. Popular but unauthoritative: "no namespace verification, no QA" (truefoundry.com, 2025). GitHub-issue submission. Free. Treat listings here as marketing surface, not a trust signal.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#PulseMCP -->
## PulseMCP

Directory with 12,630+ servers updated daily plus a Sub-Registry API implementing the Generic MCP Registry API: anyone who runs a PulseMCP-compatible endpoint becomes a federated MCP registry discoverable by conforming clients.

- **Trust model:** hybrid curation. Manual submissions via `/submit`, automated scrape+crawl with manual curation, federation with the Official Registry, optional vendor security analyses surfaced as `securityAnalysisFromVendorX.status: "pass"`, `isOfficial: true` flag.
- **Manifest:** extended `server.json`. Custom namespace `_meta.com.pulsemcp/server` carries enrichment (`visitorsEstimateLastFourWeeks`).
- **API:** `/api/docs/v0.1` (pulsemcp.com/api, 2025; pulsemcp.com/statistics).
- **Audience:** partners wanting to federate catalogs, analysts wanting ecosystem stats.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#Glama.ai — Registry + Inspector + Gateway -->
## Glama.ai (registry + inspector + gateway)

Catalog, live inspector, and request-mediating gateway in one.

- **Trust model:** quantitative quality-scoring algorithm. Indexes after automated checks, logs every call, gates tool access, supports OAuth 2.1 DCR.
- **Manifest:** `glama.json` (`$schema: https://glama.ai/mcp/schemas/server.json`).
- **Scoring formula** (glama.ai/mcp/servers/acashmoney/bio-mcp/score, 2025):
  - Overall = 70% Tool Definition Quality + 30% Server Coherence.
  - Per-tool TDQS scores 1-5 across six dimensions, weighted: Purpose Clarity 25%, Usage Guidelines 20%, Behavioral Transparency 20%, Parameter Semantics 15%, Conciseness 10%, Contextual Completeness 10%.
  - Server-level TDQS = 60% mean + 40% minimum (punishes one-great-tool + three-sloppy-tools vs flat averaging).
  - Server Coherence scored equal-weight on Disambiguation, Naming, Tool Count, Completeness.
  - Tiers: A ≥3.5, B ≥3.0, C ≥2.0, D ≥1.0, F <1.0. "B+ is passing."
- **Gates:** no LICENSE = not installable; `glama.json` required; server must be inspectable; no known vulnerabilities; author verified.
- **Audience:** authors who want a public quality ranking; consumers who want a reproducible quality signal.

> Unresolved: the source says "B+ is passing" and "B+ (Overall ≥3.0) is passing" but defines tiers A to F with B at ≥3.0 and no "B+" tier. Read as: an overall score of 3.0 or higher passes; confirm against Glama's current page.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#OpenTools -->
## OpenTools

Gateway-as-API, not a passive registry. A single OpenAI-compatible completions endpoint executes MCP tools inline: `POST https://api.opentools.com/v1/chat/completions` with `tools: [{ "type": "mcp", "ref": "google-maps" }]` (opentools.com, 2025).

- Managed connectors: "no personal API keys needed."
- Pricing: token pass-through at cost plus execution charges; unified billing.
- Audience: LLM app builders who want MCP tools without integrating an MCP client.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#MCP-Hub Verified Publishers -->
## MCP-Hub Verified Publishers

Trust-badge-as-a-service. $199/year per organization: submit certificate of incorporation + tax ID + domain ownership, 5-business-day review, green verified badge, priority listing, enterprise-policy access (mcp-hub.info/verified-publishers, 2025). Automated security audit of published MCPs. Full refund if rejected. Cross-registry: the badge is a signal, not a hosting change.
