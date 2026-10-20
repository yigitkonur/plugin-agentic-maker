---
as_of: 2026-02
verify_before_citing: true
---

# Client compatibility: documented silent-failure cases

> Read when: a user reports a "broken MCP server" and you must rule out a client quirk before debugging server code.

<!-- src: audit-agentic-mcp/references/patterns/client-compatibility.md#Documented silent-failure cases -->
## Documented silent-failure cases

1. **Cursor "No Tools Found" on wrong root key.** `.cursor/mcp.json` with `{"servers": {...}}` instead of `{"mcpServers": {...}}`. The file parses, no error log, no warning; the agent simply sees no tools. Reproduce: swap the top-level key on a working config; restart Cursor. Fix: the key must be exactly `mcpServers`.
2. **Zed prompts with >1 argument disappear.** Server advertises `code_review(path, language)`; Zed's `acceptable_prompt` filter drops it. Reproduce: register any prompt with two arguments, call `prompts/list` from Zed's MCP inspector; the prompt is absent. No UI indicator, no debug log. Fix: collapse to one JSON argument.
3. **Claude Desktop dynamic resources ignored.** Server exposes `config://app` and `greeting://{name}`; Claude Desktop's `+` menu shows only `config://app`. Identical server works in Cline. Reproduce: register one static and one templated resource; open the attach menu. Fix: expose templated URIs as tools.
4. **Cline drops `Authorization` on SSE/HTTP.** Configure a bearer token in `cline_mcp_settings.json`; tool calls arrive at the server with no `Authorization` header; server returns 401; Cline shows "Connection closed". Reproduce: tcpdump the request. Fix: none in Cline; use stdio, or wait for #4188.
5. **Cursor >40-tool silent truncation (pre-2025-09).** Six servers x 7 tools each = 42 tools; all appear enabled in the UI but calling tool #41 prompts the agent to apologize with "I cannot find a tool called...". Reproduce: exceed the cap and enumerate tools. Fix: consolidate to <=40 tools, or upgrade Cursor to 2025-09+ for the 80 cap.
6. **Claude Desktop + Cloudflare tunnel OAuth deadlock.** OAuth `/token` returns 200 then the Claude backend never POSTs to `/mcp`. Cloudflare's `cf.bot_management.managed_challenge` under "Block AI Training Bots" is the cause. Reproduce: put any origin behind Cloudflare with the AI-bot rule on, configure Claude Desktop to OAuth against it. Fix: WAF exception.

Related patterns: `client-compatibility-content-and-tools.md` (cases 1 to 3 and 5), `client-compatibility-auth-and-transport.md` (cases 1, 4, 6).
