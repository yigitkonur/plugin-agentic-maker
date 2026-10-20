# MCP common pitfalls

> Read when: you review an MCP server and want the ten most frequent mistakes with their fixes, or you need a quick pattern-match before a deeper audit.

<!-- src: audit-agentic-mcp/SKILL.md#Common pitfalls -->
## The ten pitfalls

| # | Pitfall | Fix |
|---|---|---|
| 1 | Wrapping every REST endpoint as a tool | Design around user intent (`mcp/design-*`) |
| 2 | Deeply nested JSON schemas | Flatten to one level, 3-6 params (`mcp/schemas-*`) |
| 3 | Returning raw API JSON | Curate and summarize (`mcp/responses-*`) |
| 4 | Throwing protocol errors for tool failures | Use `isError` in result content (`mcp/errors-*`) |
| 5 | No input validation | Validate server-side (`mcp/security/*`) |
| 6 | Registering 20+ tools eagerly | Progressive discovery (`decisions/tool-count.md`, `mcp/budget-*`) |
| 7 | Vague tool descriptions | Treat descriptions as prompt engineering (`mcp/descriptions-*`) |
| 8 | No live verification after edits | Use an MCP client smoke test, MCP Inspector, unit tests, or endpoint checks |
| 9 | Using SSE for new remote deployments | Streamable HTTP only (`mcp/ops-*`) |
| 10 | Ignoring session cleanup | Lifecycle management (`mcp/ops-*`) |

Each pitfall maps to a hard rule: 1 to rule 5, 2 to rule 6, 3 to rule 7, 4 to rule 8, 5 to rule 9, 6 to rule 11, 7 to rule 12, 8 to rule 15, 9 to rule 10 (see `mcp/hard-rules.md`). Pitfall 10 has no rule number.
