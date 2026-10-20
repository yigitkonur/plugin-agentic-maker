---
as_of: 2026-02
verify_before_citing: true
---

# Client compatibility: resources, prompts, tool caps, content blocks

> Read when: you ship resources, prompts, many tools, structured output, `tools/list_changed`, or `readOnlyHint` annotations and need to know where clients drop or reinterpret them. Matrices: `client-compatibility.md`.

Code for these patterns (Python, JavaScript) is in `frameworks/mcp-client-quirk-snippets.md`.

<!-- src: audit-agentic-mcp/references/patterns/client-compatibility.md#Pattern 1: Never rely on dynamic resource templates -->
## Pattern 1: Never rely on dynamic resource templates

Resource templates with URI parameters (`greeting://{name}`) are silently dropped by most consumer clients. Claude Desktop filters them out before they reach the UI; the user cannot attach them via the `+` menu. The same server works in Cline and VS Code. Tracked in python-sdk #263 as open since 2025-03.

Expose templates as tools parameterized by the same URI args.

Affected clients: Claude Desktop (confirmed), Zed (no resource subsystem at all), Copilot CLI, Codex CLI, Continue. Source: python-sdk #263 (https://github.com/modelcontextprotocol/python-sdk/issues/263).

<!-- src: audit-agentic-mcp/references/patterns/client-compatibility.md#Pattern 2: Keep tool count at or below 40 -->
## Pattern 2: Stay under the client's hard tool cap (the guidance is 20)

Cursor enforced a hard 40-tool cap from launch until 2025-09, when it was doubled to 80. Over the limit, tools appear enabled in the UI but are not callable; the agent apologizes that it "cannot find the tool." Windsurf documents a 100 cap. Claude Code does not cap but suffers context bloat of roughly 15-30k tokens per server; four servers consume about 67k before the first prompt, and community reports show many-server setups hitting about 150k tokens up-front. Tool Search (rolled out late 2025) claims a 46.9% reduction: 51k to 8.5k.

> Reconciled: the source says "46.9% reduction" and "51k to 8.5k"; from the numbers in the same file, 51k to 8.5k is an 83% reduction (8.5/51 = 16.7% remains). Both claims are kept as stated; do not cite 46.9% together with 51k to 8.5k.

Prefer aggregated "router" tools that dispatch via an `action` parameter (the Toolhost facade, see `mcp/design-*`). Active-set guidance: `decisions/tool-count.md`.

Affected clients: Cursor (hard cap), Windsurf (hard cap), Claude Code (soft but expensive). Sources: r/modelcontextprotocol "Cursor 40 to 80" (2025-09); forum.cursor.com t/67976 (2024-12); Windsurf Cascade docs (2026-02); code.claude.com server-managed-settings (2026-02).

<!-- src: audit-agentic-mcp/references/patterns/client-compatibility.md#Pattern 3: Never ship prompts that take more than one argument -->
## Pattern 3: Never ship prompts that take more than one argument

Zed's `context_store.rs::acceptable_prompt` filters out any prompt whose schema exceeds one argument. The prompt is dropped with no log and no UI indication; users see an empty prompt list. The filter has been in place since Zed's MCP support landed; the tracking issue was closed as not-planned.

Collapse multi-arg prompts into a single JSON argument, or expose the same logic as a tool. Affected clients: Zed. Sources: zed #21944 (2024-12, closed not-planned); zed PR #43523 (2025-12-16, agent-panel prompts landed).

<!-- src: audit-agentic-mcp/references/patterns/client-compatibility.md#Pattern 4: Always return a text content block alongside `structuredContent` -->
## Pattern 4: Always return a text content block alongside `structuredContent`

Cline renders `ImageContent` and structured-only responses as "Empty Response". Continue's UI does not stream progress updates even when the server emits them. Only VS Code fully round-trips structured output, annotations, and progress updates (but see the Codex CLI conflict in `client-compatibility.md`).

Dual-encode every response: a text `content` block for humans plus `structuredContent` for machines. Affected clients: Cline (ImageContent bug), Continue (no progress UI), likely others with partial rendering. Sources: cline #1865; continue #5790.

<!-- src: audit-agentic-mcp/references/patterns/client-compatibility.md#Pattern 9: Assume `tools/list_changed` is a no-op somewhere -->
## Pattern 9: Assume `tools/list_changed` is a no-op somewhere

Claude Code ignores `tools/list_changed` notifications; the tool list is captured once per session. Cursor, Windsurf, Zed, Cline, and VS Code refresh on notification. If your server adds tools after a gated unlock (auth, feature flag), either:

1. Advertise all tools at startup and return `isError: true` until unlocked, or
2. Require a session restart after unlock and surface that in the unlock tool's response.

Affected clients: Claude Code (silent no-op). Source: apify/mcp-client-capabilities v0.0.14 (2026-02).

<!-- src: audit-agentic-mcp/references/patterns/client-compatibility.md#Pattern 15: Gate `readOnlyHint` annotations on VS Code -->
## Pattern 15: Gate `readOnlyHint` annotations on VS Code

VS Code uses the `readOnlyHint` annotation to skip the confirmation dialog for read-only tools (no modal on every `search`). No other client acts on the annotation. If you mark a tool `readOnlyHint: true` you MUST ensure it has no side effects: even a write of a cache file will now skip VS Code's confirmation and the user will have no chance to block it.

Reserve the hint for pure reads. For tools that are usually read-only but sometimes write (for example cache-warming reads), leave the hint off. A pure-read example sets `readOnlyHint: true`, `idempotentHint: true`, `openWorldHint: false`.

Affected clients: VS Code (acts on hint), others ignore. Source: code.visualstudio.com/api/extension-guides/ai/mcp (2026-02).
