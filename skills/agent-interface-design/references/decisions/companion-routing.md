# Companion routing after an MCP audit or sketch

> Read when: an MCP audit finding or architecture sketch is done and you must decide which implementation, test, or non-MCP route takes over. Companions are optional: use one only if it is installed.

<!-- src: audit-agentic-mcp/references/decision-trees/companion-toolchain.md#Companion Toolchain Decision Tree | audit-agentic-mcp/references/decision-trees/companion-toolchain.md#Decision Tree -->
## Decision tree

Pick the smallest route that can finish the job. This plugin diagnoses, prescribes and routes; it does not write SDK code. A named companion skill is an optional helper, "if installed". When it is not installed, do the step yourself from the matching reference, or hand the user the finding and the validation plan.

```
START: What needs to happen after the MCP audit or architecture sketch?
|
+-- Implement a TypeScript server using mcp-use conventions?
|   +-- YES --> build-mcp-use-server (if installed)
|       Use for tools, schemas, responses, auth, sessions, transports,
|       MCP Apps widgets, ChatGPT Apps, Inspector, and deploy mechanics.
|
+-- Implement or maintain raw official SDK v1?
|   +-- YES --> build-mcp-server-sdk-v1 (if installed)
|       Use for @modelcontextprotocol/sdk v1.x, single-package imports,
|       Zod v3/raw-shape patterns, stdio, Streamable HTTP, OAuth, and v1 APIs.
|
+-- Implement or maintain raw official SDK v2?
|   +-- YES --> build-mcp-server-sdk-v2 (if installed)
|       Use only after checking current npm/docs state and confirming the user
|       accepts alpha/pre-release risk when v2 is still alpha.
|
+-- Need live verification against a running server?
|   +-- YES --> test-by-mcpc-cli (if installed)
|       Use for repeatable stdio/Streamable HTTP smoke checks, JSON scripting,
|       schema inspection, grep, and post-fix verification.
|
+-- Is the real problem CLI agent-readiness?
|   +-- YES --> audit-agentic-cli (if installed), or this plugin's CLI audit
|       Use when stdout/stderr, JSON contracts, exit codes, non-interactive
|       flags, or repairable CLI workflows are the core surface.
|
+-- Does an existing CLI or SDK already solve the workflow?
|   +-- YES --> no MCP / use existing CLI
|       Prefer CLI when shell composition, files, pipes, local trust, or an
|       already mature command contract dominates the work.
|
+-- Is the missing value static workflow knowledge rather than a runtime tool?
|   +-- YES --> use an agent skill
|       Prefer a skill when the agent needs procedure, standards, prompts, or
|       domain context, not authenticated runtime access.
|
+-- Otherwise
    +-- Keep the audit or design pass in control
        Continue the audit/architecture pass until the route is clear.
```

<!-- src: audit-agentic-mcp/references/decision-trees/companion-toolchain.md#Positive Routing Rules -->
## Positive routing rules

| Route | Pick when | Do not use for |
|---|---|---|
| `build-mcp-use-server` | `mcp-use/server` imports, HTTP-first TypeScript servers, widgets/apps, OAuth helpers | General agent-readiness audits |
| `build-mcp-server-sdk-v1` | `@modelcontextprotocol/sdk` v1 single-package servers | v2 split-package imports |
| `build-mcp-server-sdk-v2` | `@modelcontextprotocol/server` v2 split-package servers where alpha risk is accepted | Production-default raw SDK work when v2 is still alpha |
| `test-by-mcpc-cli` | Running stdio/Streamable HTTP smoke checks and JSON-scripted validation | Static design review without a running server |
| `audit-agentic-cli` | CLI command contracts and machine-readable execution surfaces | MCP protocol, schema, auth, or transport design |
| No MCP / existing CLI | Mature CLI/SDK already exposes the workflow cleanly | Multi-user auth, approval, or typed tool discovery needs |
| Agent skill | Runtime access is unnecessary; the agent needs workflow knowledge | Live external state, auth, or per-call data access |

<!-- src: audit-agentic-mcp/references/decision-trees/companion-toolchain.md#Output Line -->
## Output line

When you choose a route, include one line in the audit or architecture output:

`Companion route: <skill-or-path> because <reason>; validation: <MCP client smoke test | MCP Inspector | unit/integration test | manual check>.`

<!-- src: audit-agentic-mcp/SKILL.md#Companion skills (route fixes here) -->
## Companion skills (optional, if installed)

| Skill | When to pick | Tradeoff |
|---|---|---|
| `build-mcp-server-sdk-v1` | Production-default raw SDK with widest client compatibility, stdio or HTTP | Manual transport/OAuth wiring; deprecated overloads still compile |
| `build-mcp-server-sdk-v2` | New greenfield projects accepting v2 alpha risk after checking npm and docs | Alpha APIs can change; runtime and OAuth caveats in `fresh/mcp-framework-picker.md` |
| `build-mcp-use-server` | New HTTP-first TypeScript server wanting `mcp-use/server` conventions, widgets/apps, OAuth helpers | Locks into `mcp-use/server` imports; less bare-metal control |
| `convert-mcp-sdk-v1-to-v2` | Migrating existing SDK v1 code to v2 alpha | Targets the migration only |
| `test-by-mcpc-cli` | Repeatable stdio/Streamable HTTP smoke checks, JSON scripting, post-edit verification | Requires the `mcpc` CLI locally (the source named version 0.2.x) |
| `audit-agentic-cli` | The interface should stay CLI-first or the task is CLI agent-readiness, not MCP | CLI contract work, not MCP protocol work |

Out-of-scope routes for an MCP audit: raw `@modelcontextprotocol/sdk` v1 code goes to `build-mcp-server-sdk-v1`; raw `@modelcontextprotocol/server` v2 alpha code to `build-mcp-server-sdk-v2`; `mcp-use/server` code to `build-mcp-use-server`; live CLI smoke-testing of an MCP server to `test-by-mcpc-cli`; CLI agent-readiness to `audit-agentic-cli`; SDK v1 to v2 migration to `convert-mcp-sdk-v1-to-v2`.
