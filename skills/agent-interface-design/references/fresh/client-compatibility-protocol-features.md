---
as_of: 2026-02
verify_before_citing: true
---

# Client compatibility: sampling, instructions, elicitation, MCP Apps

> Read when: your server uses sampling, elicitation, the `instructions` field, or MCP Apps and must degrade on clients that lack them. Matrices: `client-compatibility.md`; core gating rules: `mcp/protocol-*`.

Code for the fallbacks is in `frameworks/mcp-client-quirk-snippets.md`.

<!-- src: audit-agentic-mcp/references/patterns/client-compatibility.md#Pattern 6: Treat sampling as optional, not available -->
## Pattern 6: Treat sampling as optional, not available

The `sampling/createMessage` round-trip, which lets the server ask the client to run a model call on its behalf, is supported in VS Code (1.101+, uses the user's subscription and respects `modelPreferences`), JetBrains AI, Mistral Le Chat, and a few niche clients. Every other major client returns `Method not found` or ignores the request. Claude Code's feature request is still open; Cursor declined; Cline and Copilot CLI return hard errors.

Capability-check first; fall back to a static path otherwise.

Affected clients: everyone except VS Code and a handful of partners. Sources: claude-code #1785; cline discussion #4522; GitHub community discussion 160291 (Copilot CLI); code.visualstudio.com/blogs/2025/06/12/full-mcp-spec-support.

<!-- src: audit-agentic-mcp/references/patterns/client-compatibility.md#Pattern 8: Do not put safety logic in the `instructions` field -->
## Pattern 8: Do not put safety logic in the `instructions` field

The initialize-result `instructions` string is rendered differently by every client: Claude Desktop injects it into the system prompt, Cursor appends it to the tool list, Zed treats it as a block of documentation, and VS Code surfaces it in a collapsible panel. Do not place guardrails ("never delete without confirmation") there; they will be trimmed, outranked by user prompts, or ignored entirely.

Put enforcement on the server side (require an explicit `confirm: true` parameter, or use `elicitation/create` where supported). Use `instructions` only for non-security orientation text. See also the steering tension in `decisions/steering-contract.md`.

Affected clients: all; behavior is not portable. Source: modelcontextprotocol.io specification/2025-11-25/changelog (2025-11).

<!-- src: audit-agentic-mcp/references/patterns/client-compatibility.md#Pattern 13: Emit human-readable text even when elicitation is declined -->
## Pattern 13: Emit human-readable text even when elicitation is declined

Elicitation (`elicitation/create`) lets a server pop a form in the client for structured input. VS Code (1.102+), Cursor (late 2025), Codex CLI, and Goose support it; Claude Code declined the feature as not-planned (claude-code #7108, 2025-09). When elicitation is unavailable, the request returns either `Method not found` or a capability-error, and the model has no idea what was needed.

Always fall back to a plain-text prompt-for-input embedded in the tool response, for example: "This action is destructive. Reply with `confirm=true` in the next call to proceed."

Affected clients: Claude Code, Cline, Windsurf, Zed, Copilot CLI, Continue. Sources: claude-code #7108; github.blog "MCP elicitation in Copilot" (2025-09-04).

<!-- src: audit-agentic-mcp/references/patterns/client-compatibility.md#Pattern 14: Do not assume MCP Apps (interactive UI) is portable -->
## Pattern 14: Do not assume MCP Apps (interactive UI) is portable

MCP Apps, the 2026-01 spec addition that lets servers return interactive web UI panels, is so far implemented only in VS Code (2026-01-26, Insiders to Stable). Goose is tracking it on a separate roadmap track. Everyone else ignores the content type.

If you use MCP Apps for the UI, always include an equivalent text/structured response path so the server degrades to a normal tool call on clients without MCP Apps.

Affected clients: every client except VS Code. Source: code.visualstudio.com/blogs/2026/01/26/mcp-apps-support.
