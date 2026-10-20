---
name: design
description: Design an agent-facing CLI, MCP server or skill from an idea: choose the surface, interview, sketch before any code. Started by you.
disable-model-invocation: true
argument-hint: "<what the agent should be able to do>"
allowed-tools: Bash(agentic-maker *) Bash(${CLAUDE_PLUGIN_ROOT}/bin/agentic-maker *) Read Grep Glob
---

# Design

Idea: `$ARGUMENTS`

Reference files are under `${CLAUDE_PLUGIN_ROOT}/skills/agent-interface-design/references/`; the interview and workflows are in `${CLAUDE_SKILL_DIR}/references/`. This runs in the main conversation, so ask the user directly.

Existing surfaces: !`${CLAUDE_PLUGIN_ROOT}/bin/agentic-maker detect "${CLAUDE_PROJECT_DIR}" --human 2>&1 | head -20 || true`

## Procedure

1. **Choose the surface first.** [surface-choice.md](../agent-interface-design/references/decisions/surface-choice.md): a CLI when a mature CLI exists or the agent works in a shell; an MCP server only for per-user auth or tenancy, approvals, typed remote discovery, a shared multi-client service or server-held state; a skill when the gap is workflow guidance; a hybrid when control and execution differ. Label each recommendation as documented fact, benchmark, or practitioner report. Fix an existing CLI before proposing an MCP server.
2. **Interview.** Run the question set in [interview.md](references/interview.md) (twelve questions, verbatim), one group at a time, with `AskUserQuestion`. Stop and propose defaults when the user says "whatever you think is best", and get an explicit yes.
3. **Sketch.** Start from the agent's task, then the smallest surface that serves it, then answer the eight contract questions ([contract.md](../agent-interface-design/references/contract.md)). For a CLI: the deliverables in [cli-deliverables.md](references/cli-deliverables.md) (command grammar, flags, stdout/stderr rules, envelope, exit codes, migration notes). For an MCP server: [mcp-design-workflow.md](references/mcp-design-workflow.md) (architecture sketch, tool list with Verb + Resource names, schemas, error strategy, budget).
4. **Approval gate.** Present the sketch and wait. Write no code until the user approves it; then the implementation is ordinary work, and `/agentic-maker:audit` and `/agentic-maker:derail` check it afterwards.

If a companion skill for the implementation is installed (the SDK builders are listed in [companion-routing.md](../agent-interface-design/references/decisions/companion-routing.md)), name it; do not assume it is.
