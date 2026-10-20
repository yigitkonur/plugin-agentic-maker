---
as_of: unknown
verify_before_citing: true
---

# Publish and consume how-tos per registry

> Read when: you run the actual publish or consume commands for the Official Registry, Smithery, Docker MCP Catalog, Cloudflare Remote MCP, Glama, or a PulseMCP sub-registry. CLI versions move; verify before running.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#7. Publish-and-Consume How-Tos -->
## Publish-and-consume how-tos

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#Official Registry -->
### Official Registry

```bash
# Publish
mcp-publisher login github
mcp-publisher init                       # writes server.json
mcp-publisher publish

# Alt: DNS-verified namespace
mcp-publisher login dns --domain example.com --private-key "$KEY"

# Consume
curl "https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.alice/weather"
curl "https://registry.modelcontextprotocol.io/v0.1/servers/com.example%2Fmy-server/versions/latest"

# Self-host mirror
docker run -p 8080:8080 ghcr.io/modelcontextprotocol/registry:v1.0.0
```

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#Smithery -->
### Smithery

```bash
# Publish
smithery mcp publish "https://your-server.com/mcp" \
  -n @your-org/your-server \
  --config-schema '{"type":"object","properties":{"apiKey":{"type":"string"}}}'
# Requirements: server exposes /.well-known/mcp/server-card.json
#               returns HTTP 401 (not 403) for unauth, needed for RFC 9728 OAuth discovery

# Consume
npm install -g @smithery/cli@latest
smithery auth login
smithery mcp search github
smithery mcp add https://server.smithery.ai/@smithery-ai/github
smithery tool call @smithery-ai/github createIssue '{"title":"...","body":"..."}'
```

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#Docker MCP Catalog -->
### Docker MCP Catalog

```bash
# Publish: open PR against github.com/docker/mcp-registry with server spec.
# Docker builds, signs (cosign), attaches SBOM + provenance, publishes to mcp/<name>.
# Live in the catalog within 24h.

# Consume
docker mcp catalog pull registry.example.com/mcp/team-catalog:latest
# Or browse: https://hub.docker.com/mcp
```

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#Cloudflare Remote MCP + AI Gateway -->
### Cloudflare Remote MCP and AI Gateway

Publish: build a Worker using `workers-oauth-provider`. The Worker becomes the OAuth provider to the MCP client (serves `/authorize`, `/token`, `/register`) and the OAuth client to the upstream service. Routes exposed: `/sse`, `/authorize`, `/token`, `/register`. Upstream tokens are stored encrypted in Workers KV and never handed to the MCP client.

Consume: add `{"mcpServers": {"cloudflare-api": {"url": "https://mcp.cloudflare.com/mcp"}}}` to the client config. For CI/automation, pass a Cloudflare API token as bearer. Enable Code Mode (search + execute) by appending `?codemode=search_and_execute`.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#Glama (quality-gated) -->
### Glama (quality-gated)

```bash
# Submit the GitHub repo URL via https://glama.ai/servers
# Add glama.json at repo root with {"$schema": "https://glama.ai/mcp/schemas/server.json", "maintainers": [...]}
# In the Glama admin: Claim server -> add Dockerfile -> Deploy -> Make Release
# Gate: no LICENSE = not installable. B+ (Overall >=3.0) is passing.

# Consume
curl https://glama.ai/api/mcp/v1/servers/acashmoney/bio-mcp
```

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#PulseMCP Sub-Registry (federation) -->
### PulseMCP Sub-Registry (federation)

```bash
# Consume: standard Generic MCP Registry API on a partner registry
curl "https://www.pulsemcp.com/api/v0.1/servers?search=weather"

# Publish: submit at https://www.pulsemcp.com/submit
# PulseMCP auto-enriches with _meta.com.pulsemcp/server fields
# (visitorsEstimateLastFourWeeks, securityAnalysisFromVendorX.status)

# Federate your own registry: implement /v0.1/servers, /v0.1/servers/{name}/versions/latest,
# /v0.1/servers/{name}/versions/{version} per the spec. Clients conforming to v0.1 auto-discover.
```
