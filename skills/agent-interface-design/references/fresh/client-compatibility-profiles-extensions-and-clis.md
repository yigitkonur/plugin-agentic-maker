---
as_of: 2026-02
verify_before_citing: true
---

# Client profiles: Cline, Continue, VS Code, Copilot CLI, Codex CLI, Goose

> Read when: you need a specific client's config path, transports, spec revision, or known bugs for Cline, Continue, VS Code, Copilot CLI, Codex CLI, or Goose. More clients: `client-compatibility-profiles-desktop-and-editors.md`.

<!-- src: audit-agentic-mcp/references/patterns/client-compatibility.md#Cline (VS Code extension) -->
## Cline (VS Code extension)

- **Config path:** `cline_mcp_settings.json` with `alwaysAllow: []` allow-list.
- **Tool cap:** none.
- **Spec revision:** 2025-06-18 referenced.
- **Known bugs:** Streamable HTTP regression v3.17.5+ (cline #3315, #3829); `Authorization` header not sent to SSE/HTTP servers (#3090, #4188); SSE server names rendered as `undefined` (#3837); TCP connections close after 5 minutes on SSE (#3662); `ImageContent` displayed as "Empty Response" (#1865); default MCP directory hardcoded `Documents/Cline/MCP` breaks on Japanese Windows and iCloud-synced Documents (#2762, #3501); sampling and elicitation both rejected (discussion #4522).

<!-- src: audit-agentic-mcp/references/patterns/client-compatibility.md#Continue -->
## Continue

- **Config path:** `.continue/mcpServers/*.yaml` (workspace) or hub `config.yaml`.
- **Tool cap:** none.
- **Spec revision:** "v1" (project-internal).
- **Known bugs:** MCP only active in agent mode (not chat or edit); Streamable HTTP progress updates not rendered in UI (continue #5790, closed without resolution).
- **Docs:** docs.continue.dev/customize/deep-dives/mcp.

<!-- src: audit-agentic-mcp/references/patterns/client-compatibility.md#VS Code (native MCP, Microsoft) -->
## VS Code (native MCP, Microsoft)

- **Config paths:** `.vscode/mcp.json` (workspace), user profile `mcp.json`, `devcontainer.json` under `customizations.vscode.mcp.servers`, CLI `code --add-mcp '{...}'`, or `vscode:mcp/install?{json}` web-install URL.
- **Tool cap:** none.
- **Spec revision:** 2025-06-18 (full implementation).
- **GA:** 2025-07-14 with v1.102 under org-policy gate (github.blog/changelog/2025-07-14).
- **Unique features:** annotations (`readOnlyHint` auto-approves reads); prompt-input completions; resource updates and streaming logs; elicitation; sampling using the user's model subscription respecting `modelPreferences`; roots; DCR + client-credentials fallback; MCP Apps first client (2026-01-26 Insiders to Stable).
- **Sandboxing:** enabled on macOS/Linux stdio; not on Windows.

<!-- src: audit-agentic-mcp/references/patterns/client-compatibility.md#Copilot CLI (GitHub) -->
## Copilot CLI (GitHub)

- **Config path:** `~/.copilot/mcp-config.json`.
- **Transports:** stdio / HTTP (Streamable, `type: http`) / SSE (legacy backcompat).
- **Tool cap:** `*` wildcard default; no numeric limit.
- **Spec revision:** 2025-06-18.
- **Capabilities:** tools only; no resources, prompts, sampling, elicitation, roots.
- **Commands:** `/mcp show`, `/mcp edit`, `/mcp disable`.
- **Docs:** docs.github.com/copilot/copilot-cli/add-mcp-servers; sampling rejection discussed in community 160291.

<!-- src: audit-agentic-mcp/references/patterns/client-compatibility.md#Codex CLI (OpenAI) -->
## Codex CLI (OpenAI)

- **Config path:** `~/.codex/config.toml` with `[mcp_servers.<name>]` blocks; supports `supports_parallel_tool_calls` and per-tool `[mcp_servers.<name>.tools.<tool>] approval_mode`.
- **Transports:** stdio, Streamable HTTP. SSE not supported.
- **Tool cap:** none.
- **Spec revision:** 2025-06-18+.
- **Distinctive behavior:** MCP tools run serialized by default; parallel tool calls are opt-in. Codex Cloud does not yet support MCP servers (cited proxy/credential-forwarding blockers). `codex mcp-server` exposes Codex itself as an MCP stdio server. `codex mcp login <server>` handles Streamable HTTP OAuth. `--output-schema` flag for structured output. Reference: developers.openai.com/codex/cli/reference.

<!-- src: audit-agentic-mcp/references/patterns/client-compatibility.md#Goose (Block) -->
## Goose (Block)

- **Config path:** `~/.config/goose/config.yaml`.
- **Install:** deeplink only for stdio + `uvx`; HTTP/SSE manual. Deeplink does not pass env vars.
- **Tool cap:** none.
- **Spec revision:** 2025-06-18 (partial).
- **Known behavior:** elicitation landed late 2025 (Desktop confirmed); Tasks from the 2025-11-25 spec not supported despite initial community belief (r/mcp, 2026-02). Remote-only for Streamable HTTP and SSE.
- **Docs:** gofastmcp.com/integrations/goose.
