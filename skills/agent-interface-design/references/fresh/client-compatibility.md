---
as_of: 2026-02
verify_before_citing: true
---

# MCP client compatibility: capability matrices and conflicts

> Read when: you decide which MCP features a server can rely on across clients, or you must cite what a specific client supports. Verify before citing; `?` means unverified, not absent.

Eleven major clients interpret the same wire protocol differently, often silently. Cells: `native` (fully works), `partial` (caveats), `ignored` (announced but silently dropped, or "Method not found"), `?` (unknown as of the matrix month). Issue refs are `repo #number`.

<!-- src: audit-agentic-mcp/references/patterns/client-compatibility.md#MCP Client Compatibility: Per-Client Behavior | audit-agentic-mcp/references/patterns/client-compatibility.md#Master Capability Matrix -->
## Matrix A: master capability matrix (2026-02)

Sources: apify/mcp-client-capabilities v0.0.14 (2026-02), mcp-availability.com (2026-02), per-client changelogs. In this matrix `?` = `unknown-2026-02`.

| Feature | Claude Desktop | Claude Code | Cursor | Windsurf | Zed | Cline | Continue | VS Code | Copilot CLI | Codex CLI | Goose |
|---|---|---|---|---|---|---|---|---|---|---|---|
| tools | native | native | native | native | native | native | native | native | native | native | native |
| static resources | partial (manual `+` attach) | native | native (v1.6, 2025-09) | native | ignored | native | ignored | native | ignored | ignored | native |
| dynamic resource templates | ignored (python-sdk #263) | ? | ? | ? | ignored | ? | ? | native | ? | ? | ? |
| prompts | partial (manual attach) | native (`/mcp__svr__prompt`) | native | native | native (agent panel since 2025-12) | ignored | native | native (`/mcp.server.promptname`) | ignored | ignored | native |
| sampling | ? | ignored (claude-code #1785) | ignored (forum 149604) | ignored | ignored | ignored (cline #4522) | ignored | native (1.101, 2025-06) | ignored ("Method not found") | ignored | partial |
| elicitation (form) | ? | ignored (claude-code #7108, closed not-planned 2025-09) | native (late 2025) | ignored | ignored | ignored | ignored | native (1.102+, 2025-09) | ignored | native | native (late 2025) |
| elicitation (URL mode) | ? | ? | ? | ? | ? | ? | ? | partial (Insiders) | ? | ? | ? |
| roots | ? | native | native | ignored | ignored (zed #53156) | ignored | ? | native | ignored | ignored | ignored |
| completions | ? | ? | ? | ? | ? | ? | ? | native (prompt inputs) | ? | ? | ? |
| progress notifications | ? | ? | ? | ? | ? | partial (no UI stream) | partial (no UI stream, continue #5790) | native | ? | ? | ? |
| cancellation | ? | ? | ? | ? | ? | ? | ? | native | ? | ? | ? |
| tools/list_changed | ? | ignored | native | native | native | native | ? | native | ? | ? | ? |
| annotations (readOnlyHint) | ? | ? | ? | ? | ? | ? | ? | native (auto-approve) | ? | ? | ? |
| outputSchema / structuredContent | ? | ? | ? | ? | ? | ignored (cline #1865) | ? | native | ? | native (`--output-schema`) | ? |
| OAuth 2.1 | native (PKCE/S256) | partial (basic-auth reports) | native (browser flow) | native | native | ignored (cline #3090, #4188) | ? | native | partial (header-based) | native (`codex mcp login`) | partial (via `envs`) |
| Dynamic Client Registration | ? | ? | ? | ? | ? | ignored | ? | native (with client-credentials fallback) | ? | ? | ? |
| MCP Apps (interactive UI) | ignored | ignored | ignored | ignored | ignored | ignored | ignored | native (first client, 2026-01-26) | ignored | ignored | partial (separate track) |
| stdio transport | native | native | native | native | native | native | native | native | native | native | native |
| Streamable HTTP | native | native | native | native | native | partial (regression v3.17.5+, cline #3829) | native | native | native (`type: http`) | native | partial (remote-only) |
| SSE (legacy) | ? | ? | native (legacy) | native | ? | native | native | native | native (backcompat) | ignored | partial (remote-only) |
| spec revision targeted | 2025-06-18+ | 2025-06-18+ | 2025-11-25 | >=2025-03-26 | 2025-11-25 | 2025-06-18 | "v1" | 2025-06-18 (full) | 2025-06-18 | 2025-06-18+ | 2025-06-18 (partial) |

## Matrix B: client support matrix (2025-12)

Also held, with its own provenance, in `fresh/mcp-advanced-feature-support.md`. Here `?` = `unknown-2025-12`. Sources: VS Code MCP blog 2025-06-12, GitHub Copilot elicitation blog 2025-09-04, claude-code #7108 (2025-09), GitHub community #160291 (2025-09), zed #53156 (2025-11). Codex CLI is not in this matrix.

| Feature | Claude Desktop | Claude Code | Cursor | Windsurf | Zed | Cline | Continue | VS Code (Copilot) | Copilot CLI | Goose |
|---|---|---|---|---|---|---|---|---|---|---|
| sampling | ignored | ignored (FR #1785 open) | ignored (forum 149604) | ignored | ignored | ignored (#4522) | ignored | native (1.101, 2025-06) | ignored (community #160291) | partial (2025-11) |
| sampling/tools | ? | ignored | ignored | ignored | ignored | ignored | ignored | partial (2025-11-25) | ignored | ? |
| elicitation (form) | ? | ignored (#7108 "not planned") | native (community) | ignored | ignored | ignored (#4522) | ignored | native (1.102, 2025-09) | ? | native (desktop) |
| elicitation (url) | ? | ignored | ? | ? | ? | ? | ? | partial (Insiders, 2025-11) | ? | ? |
| roots | native | native (2025-11) | ignored | ignored | ignored (#53156) | ignored | ignored | native (1.101) | ignored | native |
| completions | native | ? | ? | ? | ? | ? | ? | native (1.101) | ? | ? |
| progress | partial | ? | ? | ? | ? | ? | ? | native | ? | ? |
| cancellation | ? | ? | ? | ? | ? | ? | ? | native | ? | ? |
| `_meta` passthrough | partial | partial | partial | partial | partial | partial | partial | partial | partial | partial |

## Conflicts

No silent merge: where the matrices or their own text disagree, both claims are listed. Matrix A is newer (2026-02) than B (2025-12), which is not proof that A is right.

| Item | Claim 1 | Claim 2 |
|---|---|---|
| Claude Desktop sampling | A: `?` | B: ignored |
| Claude Desktop roots | A: `?` | B: native |
| Claude Desktop completions | A: `?` | B: native |
| Claude Desktop progress | A: `?` | B: partial |
| Cursor roots | A: native | B: ignored |
| Continue roots | A: `?` | B: ignored |
| Goose roots | A: ignored | B: native |
| Copilot CLI elicitation (form) | A: ignored | B: `?` |
| Claude Code elicitation (URL) | A: `?` | B: ignored |
| Dynamic resource templates, Copilot CLI / Codex CLI / Continue | Matrix A: `?` | Pattern 1 text lists them as affected (`client-compatibility-content-and-tools.md`) |
| Dynamic resource templates, Cline | Matrix A: `?` | Pattern 1 text: the same server works in Cline and VS Code |
| Structured output round-trip | Pattern 4 text: only VS Code fully round-trips structured output, annotations and progress | Matrix A: Codex CLI is also native for outputSchema / structuredContent (`--output-schema`) |

> Unresolved: the rows above cannot be settled from the page's own data; re-test the client before relying on either claim. Both matrices agree everywhere else (for example sampling native only in VS Code).

Patterns, profiles, silent failures: `client-compatibility-content-and-tools.md`, `-auth-and-transport.md`, `-protocol-features.md`, `-silent-failures.md`, `-profiles-desktop-and-editors.md`, `-profiles-extensions-and-clis.md` (all in `fresh/`).

<!-- src: audit-agentic-mcp/references/patterns/client-compatibility.md#How to use this reference -->
## How to use this reference

- Before shipping a server, read the matrix row by row and list every feature you use; any `ignored` or `partial` cell for a target client is a portability task.
- Run the server under at least three clients spanning the compatibility spectrum: VS Code (full spec), Claude Desktop (loose), Cline (strict bugs). That triad catches most silent failures.
- When a user reports a bug, check the documented silent-failure cases before debugging your server code: 60%+ of "broken MCP" tickets are client quirks.
- Cite the `YYYY-MM` markers in the matrix when escalating: `unknown` means unverified as of that month, not absent.
