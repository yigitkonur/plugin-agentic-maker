# MCP hard rules

> Read when: you audit or design an MCP server and need the 15 load-bearing rules, or you must cite a rule number in a finding.

<!-- src: audit-agentic-mcp/SKILL.md#Hard rules (load-bearing) -->
## The 15 rules

Rule numbers are stable; findings cite them as "rule N". Reference names ending in `-*` are file families under `mcp/`.

| # | Rule | Read next |
|---|---|---|
| 1 | Explore the codebase before asking. Run the scan helper (`agentic-maker scan mcp`) and `rg` first. | `skills/audit/references/mcp-audit-workflow.md` |
| 2 | Audit requests stop at the report. Optimize/fix requests apply edits and verify. | none |
| 3 | Every finding cites file path and line, real code or labeled assumption. | none |
| 4 | One server at a time. If multiple servers exist, inventory and ask which is in scope. | none |
| 5 | Map tools to user intent. Never wrap REST endpoints one-to-one. | `mcp/design-*` |
| 6 | Flatten schemas past one nesting level; keep at most about 6 required params. | `mcp/schemas-*` |
| 7 | Curate tool responses for LLM consumption. Never return raw upstream JSON. | `mcp/responses-*` |
| 8 | Use `isError` in result content for tool failures. Reserve protocol errors for transport. | `mcp/errors-*`, `decisions/error-strategy.md` |
| 9 | Validate all LLM input server-side; never trust generated input. | `mcp/security/*` |
| 10 | Use Streamable HTTP for new remote deployments, not SSE. | `mcp/ops-*` |
| 11 | Past about 20 tools, expose only the tools the task needs (groups or unlocking); at 40 or more use meta-tools. Do not register everything eagerly. | `decisions/tool-count.md`, `mcp/budget-*` |
| 12 | Tool descriptions are prompt engineering; treat them with care. | `mcp/descriptions-*` |
| 13 | Capability-gate sampling, elicitation, and roots; never silently drop. | `mcp/protocol-*` |
| 14 | Use OBO (on-behalf-of) with audience checks; never forward user tokens to upstream APIs. | `mcp/security/*` |
| 15 | Verify after every applied edit: run `agentic-maker probe mcp "<the command that starts the server>"` (add `--call 'tool={}'` for read-only tools) and fix what it reports; a client smoke test, the MCP Inspector or an integration test covers what a probe cannot. | `mcp/ops-*` |

Thresholds in these rules and in the decision trees are diagnostic cues, not verdicts. Rule 11 and `decisions/tool-count.md` agree: up to 20 active tools is comfortable (register them eagerly); past about 20, expose only the tools the task needs (groups or session unlocking); about 30 is a warning; 40 or more needs meta-tools (list, describe, execute).
