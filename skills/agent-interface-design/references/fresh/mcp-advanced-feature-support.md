---
as_of: 2025-12
verify_before_citing: true
---
# Client support for sampling, elicitation, roots, completions, progress and cancellation

> Read when: you must decide whether a given client will honor an advanced MCP feature, or you are quoting a client's support level.

Survey date in the source: 2025-12. Treat every cell as stale until re-checked. Core rules: `../mcp/protocol-capability-gating.md`. A second client matrix exists in `client-compatibility.md`; this file's cells were not merged with it.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Client Support Matrix (2025-12) -->
## Client Support Matrix (2025-12)

Legend: `native` = advertises the capability and implements it; `partial` = advertises but incomplete or buggy; `ignored` = silently drops or returns "Method not found"; `unknown-YYYY-MM` = not documented or tested at survey time.

| Feature | Claude Desktop | Claude Code | Cursor | Windsurf | Zed | Cline | Continue |
|---|---|---|---|---|---|---|---|
| sampling | ignored | ignored (FR #1785 open) | ignored (forum 149604) | ignored | ignored | ignored (#4522) | ignored |
| sampling/tools | unknown-2025-12 | ignored | ignored | ignored | ignored | ignored | ignored |
| elicitation (form) | unknown-2025-12 | ignored (#7108 "not planned") | native (community) | ignored | ignored | ignored (#4522) | ignored |
| elicitation (url) | unknown-2025-12 | ignored | unknown-2025-12 | unknown-2025-12 | unknown-2025-12 | unknown-2025-12 | unknown-2025-12 |
| roots | native | native (2025-11) | ignored | ignored | ignored (#53156) | ignored | ignored |
| completions | native | unknown-2025-12 | unknown-2025-12 | unknown-2025-12 | unknown-2025-12 | unknown-2025-12 | unknown-2025-12 |
| progress | partial | unknown-2025-12 | unknown-2025-12 | unknown-2025-12 | unknown-2025-12 | unknown-2025-12 | unknown-2025-12 |
| cancellation | unknown-2025-12 | unknown-2025-12 | unknown-2025-12 | unknown-2025-12 | unknown-2025-12 | unknown-2025-12 | unknown-2025-12 |
| `_meta` passthrough | partial | partial | partial | partial | partial | partial | partial |

| Feature | VS Code (Copilot) | Copilot CLI | Goose |
|---|---|---|---|
| sampling | native (1.101, 2025-06) | ignored (community #160291) | partial (2025-11) |
| sampling/tools | partial (2025-11-25) | ignored | unknown-2025-12 |
| elicitation (form) | native (1.102, 2025-09) | unknown-2025-12 | native (desktop) |
| elicitation (url) | partial (Insiders, 2025-11) | unknown-2025-12 | unknown-2025-12 |
| roots | native (1.101) | ignored | native |
| completions | native (1.101) | unknown-2025-12 | unknown-2025-12 |
| progress | native | unknown-2025-12 | unknown-2025-12 |
| cancellation | native | unknown-2025-12 | unknown-2025-12 |
| `_meta` passthrough | partial | partial | partial |

The source table was one 10-column table; it is split into two tables here only to stay readable. Cells are unchanged.

Sources named in the source: VS Code full-spec-support blog (2025-06-12); GitHub Copilot elicitation blog (2025-09-04); anthropics/claude-code #7108 (2025-09); GitHub community discussion #160291 (2025-09); zed-industries/zed #53156 (2025-11).

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 1: Capability-Gate Every Advanced Feature Before Using It -->
## Dated client statements moved out of the patterns

- Gating: GitHub Copilot CLI returns "Method not found: sampling/createMessage" for sampling (community discussion #160291, 2025-09). Claude Code closed the elicitation feature request as "not planned" (anthropics/claude-code #7108, 2025-09-04). A server that assumes support crashes on the majority of clients.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 2: Use Sampling to Keep the API Key on the Client Side -->
- Sampling: Claude Code, Cursor, Windsurf, Zed, Cline, Continue and Copilot CLI do not support sampling as of 2025-12.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 4: Use Elicitation To Clarify Missing Arguments, Not To Fish For Secrets -->
- Form elicitation: clients do not enforce the spec's ban on passwords in form mode (report from r/mcp, 2025-11).

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 5: URL-Mode Elicitation For OAuth, Secrets, And Payments -->
- URL elicitation: only VS Code Insiders advertised `elicitation.url` as of 2025-12.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 6: Honor `roots/list` Instead Of Hard-Coding Workspace Paths -->
- Roots: Zed, Cursor, Windsurf, Cline, Continue and Copilot CLI had no roots support at 2025-12; use an explicit `workspace_path` tool argument for them. (The source called this "the Pattern 12 matrix"; the matrix is the section above.)

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 7: Implement `completion/complete` With Context-Aware Narrowing -->
- Completions: most clients except Claude Desktop and VS Code do not advertise `completions`.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 8: Progress Tokens Belong In `params._meta`, Not `params` -->
- Progress: "very few MCP clients support notifications" (r/mcp, 2025); some clients drop the connection under notification floods.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 12: Detect Stateless HTTP Mode Early — Advanced Features Silently Break Without A Session -->
- Stateless HTTP: FastMCP issue #1585 (2025) documents "elicitation/sampling/etc cannot work in stateless mode"; teams hit it when moving to Cloudflare Workers or Lambda.
