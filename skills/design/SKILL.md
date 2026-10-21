---
name: design
description: Design an agent-facing CLI, MCP server or skill from an idea: choose the surface, interview, sketch before any code. Started by you.
disable-model-invocation: true
argument-hint: "<what the agent should be able to do>"
allowed-tools: Bash(agentic-maker *) Bash(${CLAUDE_PLUGIN_ROOT}/bin/agentic-maker *) Read Grep Glob
---

# Design

Idea: `$ARGUMENTS`

Reference files are under `${CLAUDE_PLUGIN_ROOT}/skills/agent-interface-design/references/`; the interviews and workflows are in `${CLAUDE_SKILL_DIR}/references/`. This runs in the main conversation, so ask the user directly.

Existing surfaces: !`${CLAUDE_PLUGIN_ROOT}/bin/agentic-maker detect "${CLAUDE_PROJECT_DIR}" --human 2>&1 | head -20 || true`

## Procedure

1. **Choose the surface first.** [surface-choice.md](../agent-interface-design/references/decisions/surface-choice.md): a CLI when a mature CLI exists or the agent works in a shell; an MCP server only for per-user auth or tenancy, approvals, typed remote discovery, a shared multi-client service or server-held state; a skill when the gap is workflow guidance; a hybrid when control and execution differ. Label each recommendation as documented fact, benchmark, or practitioner report. Fix an existing CLI before proposing an MCP server.
2. **Interview.** Use the interview for the surface chosen in step 1, in its words, one group of up to four questions at a time: an MCP server, [interview-mcp.md](references/interview-mcp.md) (twelve questions); a CLI or script, [interview-cli.md](references/interview-cli.md); a skill, [interview-skill.md](references/interview-skill.md). The closed questions go through `AskUserQuestion` with the options the file lists; the open ones are asked as plain text, because that tool offers choices, not free text. Do not put an MCP question to someone designing a CLI or a skill. Stop and propose defaults when the user says "whatever you think is best", and get an explicit yes.
3. **Sketch.** Start from the agent's task, then the smallest surface that serves it, then answer the eight contract questions ([contract.md](../agent-interface-design/references/contract.md)). For a CLI: the deliverables in [cli-deliverables.md](references/cli-deliverables.md) (command grammar, flags, stdout/stderr rules, envelope, exit codes, migration notes). For an MCP server: [mcp-design-workflow.md](references/mcp-design-workflow.md) (architecture sketch, tool list with Verb + Resource names, schemas, error strategy, budget).
4. **Approval gate.** Present the sketch and wait. Write no code until the user approves it; then the implementation is ordinary work, and `/agentic-maker:audit` and `/agentic-maker:derail` check it afterwards.

If a companion skill for the implementation is installed (the SDK builders are listed in [companion-routing.md](../agent-interface-design/references/decisions/companion-routing.md)), name it; do not assume it is.
