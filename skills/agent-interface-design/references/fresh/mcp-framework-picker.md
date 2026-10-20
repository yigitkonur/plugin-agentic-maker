---
as_of: 2026-05-09
verify_before_citing: true
---

# MCP framework picker

> Read when: you choose a TypeScript framework or SDK for a new MCP server and need the options, their transport and OAuth support, and the npm state the choice depends on.

<!-- src: audit-agentic-mcp/references/decision-trees/brainstorming-new-mcp.md#Framework Picker -->
## Framework picker

| Framework | Best for | Transport | stdio | OAuth | Maturity |
|---|---|---|---|---|---|
| **mcp-use/server** | New remote MCP in TypeScript, HTTP-first, widgets/apps, OAuth helpers, modern DX | Streamable HTTP (native), SSE fallback | No: mcp-use is HTTP-first; use the official SDK if you need stdio | Built-in OAuth helpers | GA; default for new remote servers that want its conventions |
| **Official TS SDK v1** (`@modelcontextprotocol/sdk`) | stdio MCPs, local dev tools, widest compatibility, anything shipping as `npx` | stdio + Streamable HTTP | Yes: production-default raw SDK path | BYO or via wrapper (e.g. Cloudflare `workers-oauth-provider`) | GA, widely adopted |
| **Official TS SDK v2 alpha** (`@modelcontextprotocol/server`) | New projects that want the split-package v2 API and accept pre-release risk | stdio + Streamable HTTP | Yes | Client-side only; server-side OAuth removed | **Alpha if npm still shows alpha**; not production-default. Needs Node 20+, ESM, Zod v4 |
| **SKIP: use CLI / agent skill** | Agent already has well-maintained CLI/SDK access, or static workflow guidance would suffice | N/A | N/A | N/A | N/A; see `decisions/mcp-vs-cli-evidence.md` and `decisions/companion-routing.md` |

Each framework has an optional companion build skill ("if installed"); names are in `decisions/companion-routing.md`. The source table also carried install commands for those skills from the original author's repository; they are not reproduced because they point to a personal repo.

## Check the npm state before relying on the table

```bash
npm view @modelcontextprotocol/sdk version dist-tags --json
npm view @modelcontextprotocol/server version dist-tags --json
npm view mcp-use version dist-tags --json
```

The 2026-05-09 npm check for the source revision showed `@modelcontextprotocol/sdk` `1.29.0`, `@modelcontextprotocol/server` `2.0.0-alpha.2`, and `mcp-use` `1.27.0`. Treat those as evidence for that edit, not permanent facts. If v2 still shows alpha, the default stays on v1.
