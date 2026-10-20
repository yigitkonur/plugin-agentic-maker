---
as_of: 2026-04
verify_before_citing: true
---
# Fly.io for remote MCP servers

> Read when: you are deploying an MCP server to Fly Machines with `fly mcp launch`, or want scale-to-zero with in-memory sessions.

Verify before citing: platform limits and prices change; check the vendor page.

Durable lesson: the launcher wires a bearer token to both server and client, and scale-to-zero plus in-memory sessions loses state.

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#15. Fly.io `fly mcp launch` Wires Bearer Tokens to Both Server and Client -->
## fly mcp launch and bearer tokens

`flyctl` 0.3.125+ ships a launcher that provisions a Fly Machine, sets a random bearer token as a secret, and patches the local MCP client config (Claude Desktop or Cursor) to send that token.

```bash
fly mcp launch --claude --server myapp --secret API_KEY=sk-...
```

The server gets `FLY_MCP_TOKEN` in env, with the adapter enforcing `Authorization: Bearer ${FLY_MCP_TOKEN}`. The Claude Desktop config is patched with `{"headers": {"Authorization": "Bearer ..."}}`.

- Footgun: scale-to-zero (`auto_stop_machines = true`) and in-memory sessions are incompatible. The first request after sleep gets a fresh Machine and loses session state. Externalize to Redis, Fly Postgres, or LiteFS.
- Pricing floor: `shared-cpu-1x @ 256MB` $2.02/mo; `performance-1x @ 2GB` $32.19/mo.

Sources (all accessed 2026-04): fly.io/docs/blueprints/remote-mcp-servers/; fly.io/blog/mcp-launch/; fly.io/docs/about/pricing/.
