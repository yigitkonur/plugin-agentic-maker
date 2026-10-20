---
as_of: 2025-11-25
verify_before_citing: true
---
# MCP client and SDK behaviour reported in the sources

> Read when: a rule depends on how a specific MCP client or SDK behaves (instructions field, tool-name characters, response caps, annotations, SDK method names); verify before citing.

The source does not date these reports. Specification text it cites: the MCP specification dated 2025-11-25. Core files linking here: `../mcp/descriptions-schema-split-and-examples.md`, `../mcp/schemas-coercion-and-portability.md`, `../mcp/responses-curated-and-semantic.md`, `../mcp/responses-formats-and-structured.md`, `../mcp/patterns-dynamic-tool-lists.md`, `../mcp/budget-tool-definitions.md`.

## Clients

- `instructions` (initialize response): reported as consistently read by Claude Desktop, Cursor and other major clients, unlike the spec's `prompts` feature, which many clients silently ignore.
- Tool names: several clients, including early versions of Claude Desktop, crash the whole connection when a tool name contains characters outside `[a-zA-Z0-9_]`. Reported characters: `/` crashes the Claude Desktop connection silently (some clients parse names as URI path segments); `-` breaks some tool-router middleware; `.` causes issues in OpenAI function-calling adapters; spaces are universally rejected but error messages vary; Unicode works in some clients and fails silently in others. Related tracker items cited: anthropics/claude-code#2257 (tool name validation) and modelcontextprotocol/typescript-sdk#1512 (SEP-986, tool name spec).
- Response size: Claude Code caps tool responses at 25,000 tokens.
- Content annotations (`audience`, `priority`): support varies. Well-behaved clients hide assistant-only content; others show everything.
- Inspecting definition cost: Claude Code v1.0.86+ ships a `/context` command that breaks down token usage by source; `claude-code-proxy` intercepts requests and logs full payloads.
- Dynamic tool registration: one coding agent forbids post-session tool registration to protect the prompt cache (see `prompt-caching-cases.md`).

## SDKs

- TypeScript SDK, output schemas: if a tool declares an `outputSchema` but returns only text `content`, the SDK throws a validation error at runtime; always return `structuredContent` as well.
- TypeScript SDK, registered tools: `disable()`, `enable()`, `update()` and `remove()` each send `notifications/tools/list_changed` automatically. A manual `server.notification({method: "notifications/tools/list_changed"})` is also possible. Names such as `setToolNotFoundHandler` and `notifyToolsChanged` in the source's examples are illustrative; verify against the installed SDK.
- FastMCP 3.0: layered visibility (global transforms -> session transforms -> tool-level annotations), tag-based `disable`, per-session `enable_components`, auth middleware that gates components by tag.
- Source-cited guides: FastMCP 3.0 blog and visibility docs; MCP specification (tools, `instructions`, `notifications/tools/list_changed`).
