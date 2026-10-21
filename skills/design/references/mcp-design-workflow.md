# Architect a new MCP server: workflow and output contract

> Read when: no MCP-shaped code exists yet (or the user wants a fresh server alongside an existing one) and you must produce a signed-off architecture before any implementation.

Paths below are relative to `skills/agent-interface-design/references/` unless they start with `skills/`.

<!-- src: audit-agentic-mcp/SKILL.md#Mode B — Architect a new MCP server -->
## Architect mode steps

This workflow diagnoses, prescribes and routes; it does not write SDK code.

1. Run the interview in `skills/design/references/interview-mcp.md`.
2. Choose framework and companion via `fresh/mcp-framework-picker.md` and `decisions/companion-routing.md`.
3. Cross-check the sketch with `decisions/design-phase.md` for schema portability and architecture gotchas.
4. If MCP is the wrong primitive, route to `decisions/mcp-vs-cli-evidence.md` and recommend a CLI, an agent skill, or a smaller script instead.
5. Hand off to the chosen companion (if installed) only after the architecture sketch is signed off.

**Architect output contract**

- chosen framework and companion skill
- why MCP is better than CLI, agent skill, or a smaller primitive, sourced from `decisions/mcp-vs-cli-evidence.md`
- security posture, context-budget posture, and production-readiness risks
- validation plan before and after implementation

<!-- src: audit-agentic-mcp/references/decision-trees/brainstorming-new-mcp.md#Architecture-Sketch Template -->
## Architecture-sketch template

After the 12 interview questions, produce this sketch verbatim and ask the user to approve it before any code is written.

```
# MCP Architecture Sketch — <project-name>

## Problem statement (1-2 sentences)
<end-user outcome, not API endpoints>

## User intents (1-3)
1. <intent 1>
2. <intent 2>
3. <intent 3>

## Tools (target count: <N>)
- <tool_name_1> — <one-line purpose>
- <tool_name_2> — <one-line purpose>

## Schema approach
<flat / nested / z.coerce / enum strategy — routes to mcp/schemas-*>

## Response format
<text / YAML / TSV / structuredContent — routes to decisions/response-format.md, mcp/responses-*>

## Auth
<none / API key / OAuth 2.1 + PKCE / OAuth + CIMD — routes to decisions/security-posture.md and mcp/security/*>

## Transport
<stdio / Streamable HTTP>

## Target clients
<Claude Desktop, Claude Code, Cursor, VS Code, ...>

## Framework choice
<mcp-use/server / official SDK v1 / SDK v2 alpha-if-accepted> — rationale:

## Distribution
<internal / Smithery / Docker Catalog / NPM / none> — routes to mcp/ops-*

## Success metric (3 months out)
<measurable outcome>

## Next steps
1. User approves this sketch.
2. Use the matching companion build skill if installed (decisions/companion-routing.md); otherwise implement from the references.
3. After the first tool lands, run the audit workflow (skills/audit/references/mcp-audit-workflow.md) against the prototype.
```

<!-- src: audit-agentic-mcp/SKILL.md#Execution rhythm -->
## Execution rhythm

- Audit/review request: produce the full audit report and stop. No code edits.
- Optimize/fix request with clear scope: state assumptions and tradeoffs upfront, apply in-scope edits, verify.
- Ask only when the target server is ambiguous, multiple servers are in scope and the user did not request a repo-wide audit, or the next action is destructive or externally visible.
- After every applied optimization, pick one live verification route: an MCP client smoke test, MCP Inspector, a unit/integration test, or a targeted manual endpoint check.
