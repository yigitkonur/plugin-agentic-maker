---
as_of: 2026-02
verify_before_citing: true
---

# Client profiles: Claude Desktop, Claude Code, Cursor, Windsurf, Zed

> Read when: you need a specific client's config path, tool cap, spec revision, or known bugs for Claude Desktop, Claude Code, Cursor, Windsurf, or Zed. More clients: `client-compatibility-profiles-extensions-and-clis.md`.

<!-- src: audit-agentic-mcp/references/patterns/client-compatibility.md#Per-client profiles -->
## Per-client profiles

<!-- src: audit-agentic-mcp/references/patterns/client-compatibility.md#Claude Desktop (Anthropic) -->
### Claude Desktop (Anthropic)

- **Config path:** `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS); `%APPDATA%\Claude\claude_desktop_config.json` (Windows).
- **Packaging:** Desktop Extensions (`.mcpb`) now preferred over manual JSON.
- **Tool cap:** soft (no documented hard limit).
- **Spec revision:** 2025-06-18+.
- **Known bugs:** resources and prompts announced but only reachable through the `+` attach menu; dynamic resource templates silently dropped (python-sdk #263); OAuth final POST blocked by Cloudflare AI-bot rule (reports 2025-09/11).
- **OAuth:** PKCE + S256 required, redirect to `https://claude.ai/api/mcp/auth_callback`.

<!-- src: audit-agentic-mcp/references/patterns/client-compatibility.md#Claude Code (Anthropic) -->
### Claude Code (Anthropic)

- **Config path:** `~/.claude.json` plus workspace `./.mcp.json`; not `~/.claude/settings.json` despite some docs (bug tracked 2025-11).
- **Tool cap:** none, but context bloat is severe: 4 servers ≈ 67k tokens; many servers ≈ 150k. Tool Search (late 2025) cuts ~46.9% (51k to 8.5k; see the arithmetic note in `client-compatibility-content-and-tools.md`).
- **Spec revision:** 2025-06-18+.
- **Known bugs:** server-managed settings cannot distribute MCP configs (enterprise blocker, code.claude.com server-managed-settings); `tools/list_changed` ignored; sampling and elicitation both declined (claude-code #1785, #7108).
- **Prompt invocation:** `/mcp__<server>__<prompt>`.

<!-- src: audit-agentic-mcp/references/patterns/client-compatibility.md#Cursor (Anysphere) -->
### Cursor (Anysphere)

- **Config path:** `.cursor/mcp.json` (workspace) or `~/.cursor/mcp.json` (global). Root key must be `mcpServers`.
- **Tool cap:** 40 (2024 to 2025-09), doubled to 80 (2025-09); over-limit tools silently non-callable.
- **Spec revision:** 2025-11-25 linked.
- **Known bugs/CVEs:** MCPoison (CVE-2025-54136, fixed 1.3); CurXecute (CVE-2025-54135, fixed 1.3.9); path-case (CVE-2025-59944, fixed 1.7); install-dialog spoof (CVE-2025-64106, fixed 2.0); MCP access regression reported on 2.3.41 (2025-10).
- **Resources:** supported only since v1.6 (2025-09).

<!-- src: audit-agentic-mcp/references/patterns/client-compatibility.md#Windsurf (Codeium) -->
### Windsurf (Codeium)

- **Config path:** `~/.codeium/windsurf/mcp_config.json`. Supports `${env:VAR}` and `${file:/path}` interpolation.
- **Tool cap:** 100 (explicit hard limit).
- **Spec revision:** ≥2025-03-26.
- **Known bugs:** `Authorization` header is case-sensitive; lowercase is dropped. Windows 11 + local `npx @upstash/context7-mcp` triggers an infinite Marketplace refresh loop (upstash/context7 #829, 2025).

<!-- src: audit-agentic-mcp/references/patterns/client-compatibility.md#Zed -->
### Zed

- **Config path:** `settings.json` under the `"context_servers"` key (divergent from everyone else).
- **Tool cap:** none documented.
- **Spec revision:** 2025-11-25 linked.
- **Known bugs:** prompts with more than one argument are filtered out silently in `context_store.rs::acceptable_prompt` (zed #21944); agent-panel prompt support only since PR #43523 (2025-12-16); no resources, no roots (feature request zed #53156 open); mixed `command`-string vs `command`-object shapes cause parse failures.
