---
as_of: 2026-02
verify_before_citing: true
---

# Client compatibility: auth headers, config keys, transports, OAuth

> Read when: a remote MCP server works in one client but not another (401s, "Connection closed", "No Tools Found", OAuth that succeeds then hangs) or you ship installers and OAuth.

Code (JavaScript installer branch, Python `whoami` tool) is in `frameworks/mcp-client-quirk-snippets.md`. Matrices: `client-compatibility.md`.

<!-- src: audit-agentic-mcp/references/patterns/client-compatibility.md#Pattern 5: Send `Authorization` with exact header casing -->
## Pattern 5: Send `Authorization` with exact header casing

Windsurf's HTTP client is case-sensitive on `Authorization`; `authorization` (lowercase) is dropped during request construction. Cline goes further: it does not forward the `Authorization` header to SSE or Streamable HTTP servers at all (multiple open issues). Servers then return 401, Cline surfaces "Connection closed", and users blame the server.

On the server, log the resolved auth header on startup and expose a `whoami`-style tool that echoes the received header names so operators can confirm end to end.

Affected clients: Windsurf (case bug), Cline (full drop). Sources: cline #3090; cline #4188; Windsurf header casing in docs.windsurf.com/windsurf/cascade/mcp field examples (2026-02).

<!-- src: audit-agentic-mcp/references/patterns/client-compatibility.md#Pattern 7: Branch on the config root key in installers -->
## Pattern 7: Branch on the config root key in installers

Every client except Zed consumes a top-level `"mcpServers"` key. Zed uses `"context_servers"` under `settings.json`; feeding it `"mcpServers"` yields no error and no servers. Cursor silently ignores any file whose root key is not exactly `"mcpServers"`: a typo of `"servers"` produces "No Tools Found" with nothing in logs.

If you ship an installer or deeplink, branch on the target client.

Affected clients: Zed (divergent key), Cursor (strict match). Sources: zed.dev/docs/assistant/model-context-protocol; truefoundry.com Cursor MCP setup guide (2025).

<!-- src: audit-agentic-mcp/references/patterns/client-compatibility.md#Pattern 10: Prefer Streamable HTTP, keep an SSE fallback for one more release -->
## Pattern 10: Prefer Streamable HTTP, keep an SSE fallback for one more release

The 2025-06-18 spec deprecates SSE. Codex CLI has already dropped SSE entirely. VS Code, Copilot CLI, Cursor, and Cline still accept SSE for backcompat. Goose supports only remote transports for SSE/HTTP; local stdio is recommended. Cline regressed Streamable HTTP in v3.17.5+: servers that worked on 3.17.4 disconnect after seconds on 3.17.5.

Serve both transports from the same origin, advertise Streamable HTTP first, and log a deprecation warning when SSE is used so you can retire it. (New remote servers use Streamable HTTP only: `mcp/hard-rules.md` rule 10.)

Affected clients: Codex CLI (SSE gone), Cline (HTTP regression), Goose (remote-only for both). Sources: modelcontextprotocol.io specification/2025-11-25/changelog; cline #3829; developers.openai.com/codex/cli/reference (2026-02).

<!-- src: audit-agentic-mcp/references/patterns/client-compatibility.md#Pattern 11: Never assume OAuth 2.1 DCR works -->
## Pattern 11: Never assume OAuth 2.1 DCR works

Dynamic Client Registration (RFC 7591) is only verified in VS Code, which also implements a client-credentials fallback when DCR is unavailable. Claude Desktop requires PKCE + S256 but pre-registered clients only. Cline drops auth entirely on HTTP. Copilot CLI uses header-based auth with no DCR.

For remote servers, publish both:

- OAuth 2.1 PKCE with a pre-registered client ID (works in Claude Desktop, Cursor, Windsurf, Zed)
- Static bearer token via `Authorization` header (works in Copilot CLI, Codex CLI, fallback for Cline users who patched around #3090)

Document both in your README; do not rely on DCR alone.

> Reconciled: the sources vary on DCR versus Client ID Metadata Documents (CIMD); the stance used here is to prefer CIMD where the client supports it, keep DCR for clients without it, and detect support from the authorization-server metadata instead of assuming either.

Affected clients: all except VS Code for DCR; Cline for OAuth at all. Sources: code.visualstudio.com/api/extension-guides/ai/mcp; cline #3090.

<!-- src: audit-agentic-mcp/references/patterns/client-compatibility.md#Pattern 12: Bypass Cloudflare AI-bot blocking on remote endpoints -->
## Pattern 12: Bypass Cloudflare AI-bot blocking on remote endpoints

Claude Desktop's OAuth flow completes the `/token` call (200) but the final POST to `/mcp` never arrives when Cloudflare's "Block AI Training Bots" managed rule is enabled on the origin. Users see OAuth succeed, then the connection silently hangs. Disable the Cloudflare AI-bot rule for the MCP path, or add a WAF exception for `User-Agent: Claude-User` and Anthropic IP ranges.

Affected clients: Claude Desktop (confirmed 2025-09 and 2025-11 reports). Source: r/mcp "after successful auth Claude never connects" (2025-11).
