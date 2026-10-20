# New MCP server interview

> Read when: the user says "I want to build an MCP server" and the repo has no MCP yet. Run this interview before any code or other decision tree.

Paths in this file are relative to `${CLAUDE_PLUGIN_ROOT}/skills/agent-interface-design/references/`, except `mcp-design-workflow.md`, which sits beside this file.

<!-- src: audit-agentic-mcp/references/decision-trees/brainstorming-new-mcp.md#Brainstorming a New MCP from Scratch | audit-agentic-mcp/references/decision-trees/brainstorming-new-mcp.md#Decision Tree -->
## Decision tree

The interview collects intent, converts it to an architecture sketch (`mcp-design-workflow.md`), picks a framework (`fresh/mcp-framework-picker.md`), and routes to a companion build skill if one is installed (`decisions/companion-routing.md`).

```
START: User wants to build a new MCP server
|
+-- Q1: End-user task in one sentence?
|   +-- unclear / restates the API  --> pause; run the design-phase question set first
|                                       (decisions/design-phase.md)
|
+-- Q2: Does an official CLI / well-maintained SDK already cover it?
|   +-- YES --> read decisions/mcp-vs-cli-evidence.md; MCP may not be the primitive
|   +-- NO  --> continue
|
+-- Q3: Local or remote?
|   +-- Local stdio (user's machine, one process)
|   |   --> Official TS SDK v1 (stdio-canonical)
|   |   --> use the SDK v1 build companion if installed
|   +-- Remote HTTP
|       +-- New project, HTTP-first, want modern DX --> mcp-use/server (use its build companion if installed)
|       +-- Mixed stdio + HTTP, widest compatibility --> Official TS SDK v1 (SDK v1 build companion if installed)
|       +-- Willing to accept alpha/pre-release risk  --> Official TS SDK v2 (check fresh/mcp-framework-picker.md first)
|
+-- Q4..Q12: auth, stateful, clients, tool count, destructive, distribution, advanced features, success metric
|
+-- OUTPUT: architecture sketch (template in mcp-design-workflow.md). Request user approval before any code is written.
```

<!-- src: audit-agentic-mcp/references/decision-trees/brainstorming-new-mcp.md#Interview Questions (ask verbatim; adapt only to reference user-supplied context) -->
## Interview questions (ask verbatim; adapt only to reference user-supplied context)

1. **User intent** — "Describe the outcome your users want, not endpoints. What is the end-user task this MCP enables in one sentence?"
2. **Target consumer** — "Who connects to this MCP? Solo developer, one internal team (<=10 people), B2B SaaS customers (scoped per tenant), or a public marketplace?"
3. **Underlying service** — "Does the system you're wrapping already have an official CLI (`gh`, `kubectl`, `aws`, `az`, `stripe`) or a well-maintained SDK? If yes, read `decisions/mcp-vs-cli-evidence.md` first — MCP may not be the right primitive."
4. **Local vs remote** — "Is the MCP running on the user's machine (stdio, one process) or hosted somewhere (HTTP)? Almost everything new in 2026 is remote Streamable HTTP; stdio is local dev tools."
5. **Auth profile** — "How does the server know who the caller is? (a) no auth / single-user local, (b) static API key env var, (c) OAuth 2.1 + PKCE for multi-user, (d) OAuth + CIMD/DCR for public marketplace."
6. **Stateful or stateless** — "Does any tool need to remember state across calls within a session? If no, default to stateless — avoids session-management complexity."
7. **Target clients** — "Which MCP clients must this support? Claude Desktop/Code only, or cross-client (Cursor, Windsurf, VS Code)? Some features only work in VS Code — see `fresh/client-compatibility.md`."
8. **Expected tool count** — "How many tools do you expect at launch? At 1 year? Over 20 = consider toolsets or a Codemode `search`/`execute` pair; see `decisions/tool-count.md` and `decisions/mcp-vs-cli-evidence.md`."
9. **Destructive operations** — "Will any tool mutate external state, send messages, or delete data? Those need guard params or human-confirmation flows; see `decisions/error-strategy.md` and `decisions/steering-contract.md`."
10. **Distribution** — "Where will this MCP live? Internal only, Smithery/Glama marketplace, Docker MCP Catalog, NPM, or no distribution (git clone)?"
11. **Advanced protocol features** — "Do you need sampling or elicitation? If yes, client support is uneven — see `mcp/protocol-*` before committing."
12. **Success metric** — "How will you know this MCP is working 3 months from now? Tool-call success rate, task completion in <N steps, cost per session, user retention."

Paths in the questions are relative to ``. Q5(d): detect CIMD or DCR support from the authorization-server metadata instead of assuming either; prefer Client ID Metadata Documents where the client supports them (see `mcp/security/*`).

> Reconciled: the sources treated CIMD and DCR differently in different places; this file keeps the question as written and the stance is: prefer CIMD where the client supports it, keep DCR for clients without it, never assume either.

<!-- src: audit-agentic-mcp/references/decision-trees/brainstorming-new-mcp.md#Routing After This Tree -->
## Routing after the interview

Paths relative to ``.

- Tool granularity and intent-based design: `decisions/design-phase.md`
- Tool count >10, progressive discovery, toolsets: `decisions/tool-count.md`
- Response format choice: `decisions/response-format.md`
- Auth / threat model depth: `decisions/security-posture.md`, `mcp/security/*`
- Scaling and multi-server composition: `decisions/scaling.md`, `mcp/design-*`
- Production readiness: `decisions/production-readiness.md`, `mcp/ops-*`
- Companion skill or non-MCP route: `decisions/companion-routing.md`
- CLI / agent skills / bash would dominate: `decisions/mcp-vs-cli-evidence.md`
- Client feature parity (sampling, elicitation, VS Code extras): `fresh/client-compatibility.md`, `mcp/protocol-*`
- Destructive / approval flows: `decisions/error-strategy.md`, `decisions/steering-contract.md`

<!-- src: audit-agentic-mcp/references/decision-trees/brainstorming-new-mcp.md#When to Re-evaluate -->
## When to re-evaluate

- Tool count crosses the next cliff (10 / 20 / 40 / 100): revisit `decisions/tool-count.md` and `decisions/mcp-vs-cli-evidence.md`.
- Target-client mix changes (Cursor or Windsurf added): re-check `fresh/client-compatibility.md`.
- Sampling or elicitation discovered mid-build: `mcp/protocol-*`.
- Cost per session exceeds budget: `mcp/budget-*` and `decisions/mcp-vs-cli-hybrids.md`.
- Single-user scope grows to multi-tenant: `decisions/security-posture.md` and `mcp/security/*` (OBO / CIMD).
- Trust incident or security concern: `mcp/security/*` (threat catalog).
- SDK v2 npm dist-tags or official docs change: re-read `fresh/mcp-framework-picker.md`; if v2 remains alpha, consider falling back to v1.
