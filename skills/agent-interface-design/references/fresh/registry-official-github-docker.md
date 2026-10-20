---
as_of: 2026-07-04
verify_before_citing: true
---

# Registries: Official MCP Registry, GitHub MCP Registry, Docker MCP Catalog

> Read when: you publish to, mirror, or rely on the official, GitHub, or Docker catalogs and need their trust model, manifest, namespace, and publish path. Verify before citing.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#1. Registries — the Catalog Tier -->
## Registries: the catalog tier

Catalogs index metadata and own names; they do not run tool calls. Community catalogs: `registry-community-catalogs.md`.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#Official MCP Registry — `registry.modelcontextprotocol.io` -->
## Official MCP Registry (`registry.modelcontextprotocol.io`)

Positioned as "DNS for MCP": open metadata API, no hosting, no code execution. Donated to LF AAIF 2025-12-09.

- **Trust model:** namespace authentication via GitHub OAuth, GitHub Actions OIDC, DNS TXT record, or HTTP `/.well-known/mcp-registry-auth` (modelcontextprotocol.io/registry/authentication, 2025-10). Scanning delegated to downstream aggregators.
- **Manifest:** `server.json`. Name format reverse-DNS: `io.github.alice/weather-server` for GitHub-authed publishers, `com.example/server` for DNS-verified.
- **Versioning:** each entry has an opaque stable UUID that never changes even when name or metadata change. Semver in the `version` field. API endpoints: `GET /v0.1/servers`, `GET /v0.1/servers/{serverName}/versions/latest`, `GET /v0.1/servers/{serverName}/versions/{version}`. Flat URL encoding: `com.example%2Fmy-server`.
- **Pricing:** free.
- **Audience:** downstream aggregators, sub-registry operators, enterprise mirrors. Not a user-facing portal.
- **Publish:** `mcp-publisher login github && mcp-publisher init && mcp-publisher publish`. DNS auth: `mcp-publisher login dns --domain example.com --private-key "$KEY"`.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#GitHub MCP Registry — `github.com/mcp` -->
## GitHub MCP Registry (`github.com/mcp`)

Curated discovery portal, launched 2025-09-16 (github.blog changelog 2025-09-16). Copilot Business/Enterprise customers configure which registry feeds their org.

- **Trust model:** editorial curation. Forward statement: "working with the MCP steering committee on the OSS MCP Registry to eventually allow self-publication."
- **Enterprise path:** host the OSS registry in Docker or a fork, or use Azure API Center (managed, CORS + governance; free tier basic, Standard tier for higher limits) as the GitHub-recommended managed option.
- **Required spec:** v0.1 endpoints (`GET /v0.1/servers`, `/v0.1/servers/{name}/versions/latest`, `/v0.1/servers/{name}/versions/{version}`). v0 unstable: do not implement.
- **Audience:** Copilot-first organizations.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#Docker MCP Catalog + Registry -->
## Docker MCP Catalog and Registry

Curated catalog of signed, containerized MCP servers. The only platform in the source shipping cryptographic signatures, SBOMs, and provenance by default.

- **Trust model:** Docker-built images include cosign signatures, SBOM, build provenance. Container isolation is the default runtime. Non-compliant servers can be reviewed or removed (docs.docker.com/ai/mcp-catalog-and-toolkit/catalog/, 2025).
- **Manifest:** OCI reference; submission is a PR to `github.com/docker/mcp-registry` (2025).
- **Namespace:** Docker Hub `mcp/` organization.
- **Versioning:** standard OCI tags.
- **Pricing:** free.
- **Publish:** open a PR with the server spec; Docker builds, signs, publishes, live within 24h. Self-provided pre-built images skip signing.
- **Audience:** mainstream developers, enterprises that already run Docker, anyone who needs cryptographic supply-chain assurances.
