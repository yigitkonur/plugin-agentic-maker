---
as_of: 2026-07-04
verify_before_citing: true
---
# MCP gateway, composition framework and OpenAPI-proxy products

> Read when: you need named products for a gateway, a composition framework or an OpenAPI-to-MCP proxy, instead of the vendor-neutral patterns.

The source gives no date for these names; verify that each product exists, is maintained and still works as described before citing. The vendor-neutral patterns are in `../mcp/ops-gateway.md` and `../mcp/ops-composition-patterns.md`.

<!-- src: audit-agentic-mcp/references/patterns/composition.md#6. Use a Gateway/Proxy for Multi-Server Orchestration -->
## Existing gateway solutions

- **MCPJungle:** multi-server management with prefixed naming and health checks. https://github.com/mcpjungle/MCPJungle
- **MCPX:** discovery and installation tool for MCP servers.
- **MetaMCP:** control plane for managing MCP server fleets. https://metamcp.com

<!-- src: audit-agentic-mcp/references/patterns/composition.md#7. Zero-Trust Policy Gateway -->
## Policy gateway pattern

The zero-trust policy gateway (declarative `policy.json`, HMAC job tickets, audit log) is attributed to the Stacklok policy gateway pattern: https://stacklok.com

<!-- src: audit-agentic-mcp/references/patterns/composition.md#4. Use the Provider + Transform Architecture for Maximum Flexibility | audit-agentic-mcp/references/patterns/composition.md#1. Use a Meta-Server for Cross-Cutting Concerns -->
## FastMCP 3.0 provider and transform architecture

The source describes FastMCP 3.0 as introducing Components, Providers and Transforms:

- Providers: `FileSystemProvider("./admin_tools", reload=True)`, `OpenAPIProvider(<openapi.json url>)`, `MCPClientProvider(<remote MCP url>)`, `SkillsProvider("./skills/")`.
- Transforms: `mcp.mount(provider, prefix="github")`, `VersionFilter(select="latest")`, `AuthGate(tags={"admin"}, scopes={"super-user"})`, `RenameTransform({...})`, `AuthMiddleware(tag="all", scopes={"authenticated"})`.
- Gateway form: `mcp.mount(server, namespace="github")`.

Class and function names are version-specific; check the current FastMCP documentation. Code is in `../frameworks/mcp-python/composition.md`. Announcement: https://jlowin.dev/blog/fastmcp-3

<!-- src: audit-agentic-mcp/references/patterns/composition.md#5. Generate MCP Servers from OpenAPI Specs -->
## OpenAPI proxy example

Notion's MCP server loads an OpenAPI spec and creates an `MCPProxy` that exposes every endpoint as a tool automatically: https://github.com/makenotion/notion-mcp-server. Code is in `../frameworks/mcp-ts/composition.md`.

## Example gateway server package names

The gateway configuration example uses `@anthropic/web-search-mcp` and `postgres-mcp-server` as `npx` packages; treat them as placeholders and confirm they exist before use.
