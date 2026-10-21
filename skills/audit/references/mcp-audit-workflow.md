# Audit an existing MCP server: workflow and output contract

> Read when: MCP-shaped code already exists and the user asks to audit, review, optimize, harden, or score it for agent-readiness.

Paths relative to `skills/agent-interface-design/references/` unless they start with `skills/`. The scoring rubric is not defined here; it lives in `skills/audit/references/scoring.md`.

<!-- src: audit-agentic-mcp/SKILL.md#audit-agentic-mcp — Audit, Optimize, Architect MCP Servers -->
## What this workflow does

It is the agent-readiness front door for MCP servers. It decides what is wrong, what should change, which reference applies, which companion route (if installed) implements the fix, and how to verify the result. It does not write SDK code: it diagnoses, prescribes, and routes.

<!-- src: audit-agentic-mcp/SKILL.md#When to use -->
## When to run it

Trigger on requests such as: "audit my MCP server", "review this MCP server", "is my MCP server agent-ready?"; "optimize my MCP server", "my agent keeps misusing this tool, what's wrong?"; "design a new MCP server", "should this be an MCP or a CLI?"; "score this MCP server's tool design / schemas / auth / context budget"; "my MCP server returns too much context", "my agent picks the wrong tool"; "harden my MCP server", "production-readiness check for MCP"; "which MCP framework should I pick: SDK v1, SDK v2, or `mcp-use`?".

Do not use it for writing raw SDK code, live smoke-testing, CLI agent-readiness, or SDK migration; those go to the optional routes in `decisions/companion-routing.md`. New servers go to `skills/design/references/mcp-design-workflow.md`.

<!-- src: audit-agentic-mcp/SKILL.md#Two modes -->
## Two modes

- Audit / optimize an existing server: this file.
- Architect a new server: `skills/design/references/mcp-design-workflow.md`.

<!-- src: audit-agentic-mcp/SKILL.md#Mode A — Audit / optimize an existing MCP server -->
## Audit / optimize mode steps

Pick this when MCP-shaped code already exists.

1. **Explore.** Start with the helpers: `bin/agentic-maker scan mcp <target>` (locates files; regex over source) and `bin/agentic-maker probe mcp <target> --budget` (measures a real `tools/list` response). Then confirm with direct searches:
   ```bash
   tree . -I node_modules --dirsfirst -L 3
   rg -n -l "McpServer|FastMCP|server\.tool|@tool|@mcp\.tool|registerTool|Server\(" . -g '!node_modules'
   rg -n "server\.tool|@tool|registerTool|def .*tool|tool\(" . -g '!node_modules'
   rg -n -l "z\.|inputSchema|BaseModel|Field\(|pydantic|jsonschema" . -g '!node_modules'
   rg -n "stdio|streamable|sse|transport" . -g '!node_modules'
   ```
   If `tree` is missing, `find . -maxdepth 3 -type d`. If `rg` is missing, `grep -R`. If no MCP-shaped code exists after checking root and likely server dirs (`src/`, `server/`, `servers/`, `app/`, `apps/`, `packages/`, `services/`, `mcp/`), report the missing prerequisite and switch to architect mode only if the user actually wants a new server.
2. **Detect framework, then route mechanics.** Read manifest, entry point, tool registration, schemas, transport/auth config. Keep this workflow on audit reasoning; route implementation mechanics to `decisions/companion-routing.md`.
3. **Score and prioritize.** Produce the audit output contract below. Tie every finding to real evidence or a labeled assumption. Thresholds in references are diagnostic cues, not verdicts.
4. **Apply only in implementation scope.** For optimize/fix, edit the in-scope findings and verify with one live route. For audit/review, stop at the report.

**Audit output contract**

- target path and detected framework
- the scorecard from `scoring.md`: the eight dimensions of the contract (intent, contract, discovery, steering, safety, budget, recovery, verification), each a score or `not measured`; file the usual MCP topics under them (tool interface and architecture under intent; schemas and responses under contract; security/auth under safety; context/cost under budget; errors under recovery; ops/testing under verification; client compatibility under discovery)
- prioritized findings, each with severity, evidence path/line, impact, recommended fix, companion-skill route
- verification plan: an MCP client smoke test, MCP Inspector, unit/integration, or a targeted manual check
- assumptions and items not touched

<!-- src: audit-agentic-mcp/SKILL.md#Minimal read sets -->
## Minimal read sets

Do not load the whole reference tree by default. Start with the smallest bundle.

| Work | Read first |
|---|---|
| Existing-server quick audit | the `scan mcp` and `probe mcp --budget` output, `mcp/design-*`, `mcp/schemas-*`, `mcp/responses-*`, `mcp/errors-*`, `mcp/ops-*` (testing) |
| Security / auth audit | `decisions/security-posture.md`, `mcp/security/*` (generic defenses, auth and identity, threat catalog) |
| Context / cost audit | the `probe mcp --budget` output, `mcp/budget-*` (context engineering, caching economics, progressive discovery), `decisions/tool-count.md` |
| New-server architecture | `skills/design/references/interview-mcp.md`, `decisions/companion-routing.md`, `decisions/design-phase.md`, `decisions/mcp-vs-cli-evidence.md` |

Rules that apply to every finding: `mcp/hard-rules.md`. Common mistakes to pattern-match first: `mcp/pitfalls.md`.
