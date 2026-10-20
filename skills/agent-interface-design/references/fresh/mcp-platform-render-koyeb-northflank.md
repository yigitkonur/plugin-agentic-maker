---
as_of: 2026-04
verify_before_citing: true
---
# Render, Koyeb and Northflank for MCP

> Read when: you use Render's MCP API key, or want scale-to-zero remote MCP on Koyeb or Northflank.

Verify before citing: platform limits and prices change; check the vendor page.

Durable lesson: treat Render's MCP key as a root token; on scale-to-zero container hosts run the transport stateless. Code is in `../frameworks/mcp-ts/deployment-platforms.md`.

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#18. Render's MCP API Key is Account-Wide — Treat It Like a Root Token -->
## Render MCP API key scope

Render's own MCP server (for managing Render infrastructure via an agent) uses an API key that is **broadly scoped across every workspace the key owner belongs to**. There is no per-workspace or per-service scoping primitive. A single leaked key means full account compromise.

- Never commit the Render MCP key to any repo or pass it to an untrusted agent.
- Rotate the key when moving between workspaces or organizations.
- Prefer short-lived, human-in-the-loop agent sessions for Render MCP; do not run it in unattended CI.

For your own MCP servers hosted on Render (not Render's MCP API), use the standard Render web service plus persistent disk pattern. Render gives you a managed HTTPS endpoint, auto-scaling, and a free tier; no MCP-specific quirks apply.

Sources: render.com/docs/mcp-server (accessed 2026-04); github.com/render-oss/render-mcp-server v0.3.0 (2026-01-14).

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#19. Koyeb & Northflank: Scale-to-Zero Remote MCP with `sessionIdGenerator: undefined` -->
## Koyeb and Northflank stateless transport

Both platforms offer scale-to-zero container hosting and published Streamable HTTP MCP recipes. Run the transport in **stateless mode** (`sessionIdGenerator: undefined`, no server-issued session IDs) so cold starts do not strand sessions.

```bash
koyeb deploy . my-mcp/main --git github.com/me/my-mcp-server \
  --ports 8080:http --routes /:8080 --min-scale 0 --max-scale 5 --instance-type free
```

Northflank uses a Combined Service with HTTP port 8080, optional `/health`, and runtime env vars. Both give `.koyeb.app` / `.northflank.app` hostnames. If you need state, either set min-scale 1 or back with Redis/Upstash.

Sources: koyeb.com tutorial on remote MCP over Streamable HTTP (2025-05-05); northflank.com blog on building and deploying an MCP server (2025-08-26).
