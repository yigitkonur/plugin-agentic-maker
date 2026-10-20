---
name: audit
description: Audit an agent-facing surface - a CLI, script, MCP server or skill - against the agent-interface contract, running read-only probes where it can. Produces a scored report and changes nothing. Started by the user.
disable-model-invocation: true
argument-hint: "<CLI binary path | MCP command or config | skill directory>"
context: fork
allowed-tools: Bash(agentic-maker *) Bash(${CLAUDE_PLUGIN_ROOT}/bin/agentic-maker *) Read Grep Glob
---

# Audit

Target: `$ARGUMENTS`

Paths in the references are relative to the plugin root `${CLAUDE_PLUGIN_ROOT}`; the reference files are under `${CLAUDE_PLUGIN_ROOT}/skills/agent-interface-design/references/`.

Surfaces in this project: !`${CLAUDE_PLUGIN_ROOT}/bin/agentic-maker detect "${CLAUDE_PROJECT_DIR}" --human 2>&1 | head -25 || true`

Machine: !`${CLAUDE_PLUGIN_ROOT}/bin/agentic-maker doctor --human 2>&1 | head -6 || true`

You audit; you do **not** edit anything. This runs in a fork with no conversation and no way to ask the user, so:

- If the target above is empty or unclear, return the surface list above and the line "rerun with a target", and stop.
- If you must assume something, say so under "Assumptions", never silently.

## Procedure

1. **Name the kind** from the target: an executable file or a command name -> CLI; an MCP config, command or URL -> MCP server; a directory with `SKILL.md` -> skill; a directory with `.claude-plugin/plugin.json` -> plugin (audit each skill and agent).
2. **Probe at runtime first.** Static reading only locates; the probe observes.
   - CLI or script: **your first Bash call is `agentic-maker probe cli <binary>`, and you never run the target yourself** (no `ls`, `cat`, `head`, `file` or `<binary> --help` on it: the probe reads it and runs `--help` for you, safely). Its reply contains the help text, `suggested_safe` read-only commands, and a ready `next_actions` command. Run that command, adding arguments for the read commands that need them, e.g.
     `agentic-maker probe cli <binary> --safe "list --json" --safe "get 1 --json" --safe "get missing --json # expect-exit 3" --sub "<subcommand>"`.
     The probe runs only `--help`, `--version`, one invalid command and the arguments you gave with `--safe`. **Never put a command that creates, updates, deletes, deploys, logs in, pushes, sends or installs in `--safe`.** If unsure, leave it out and list it under "Not run". One command per Bash call; if a call is denied, say which and carry on with the probe, not by running the target.
   - MCP server: `agentic-maker probe mcp <command or url> --budget` (the real `tools/list`), and `agentic-maker scan mcp <path>` to locate the registrations in source.
   - Skill: read `SKILL.md` and each file it links. Evidence about behaviour needs a run: recommend `/agentic-maker:derail <path>` rather than guessing.
3. **Apply the contract** ([contract.md](../agent-interface-design/references/contract.md)) and the rubric for the kind: CLI [checks.md](../agent-interface-design/references/cli/checks.md) and [cli-audit-workflow.md](references/cli-audit-workflow.md); MCP [hard-rules.md](../agent-interface-design/references/mcp/hard-rules.md) and [mcp-audit-workflow.md](references/mcp-audit-workflow.md). Every finding cites a probe output, a `path:line`, or is labelled an assumption.
4. **Score and report** with [scoring.md](references/scoring.md) and [report.md](references/report.md): severity in agent terms (Critical / High / Medium / Low), evidence, impact, fix, how to verify.

Return the report as your final message. State what was executed (the probe lists the exact commands), what was deliberately not run, and what the probe cannot prove. A fix is a separate, explicit step in the main conversation, verified by running the same probe again.
