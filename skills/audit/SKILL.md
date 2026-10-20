---
name: audit
description: Audit a CLI, script, MCP server or skill for agent use with read-only probes. Reports; changes nothing. Started by you.
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
   - MCP server: `agentic-maker probe mcp "<command>" --call 'tool={}'` (the real `tools/list`; add `--call` only for tools that are read-only, with real arguments), then `agentic-maker scan mcp <file or directory>` to locate the registrations in source. The reply is compact on purpose; add `--full` for the per-tool table and read the whole reply, not a truncated one.
   - Skill: read `SKILL.md` and each file it links. Evidence about behaviour needs a run: recommend `/agentic-maker:derail <path>` rather than guessing.
3. **Read the rubric, then judge.** Use the Read tool on these files before you write a word of the report (they are short):
   - `${CLAUDE_PLUGIN_ROOT}/skills/agent-interface-design/references/contract.md` (the eight questions),
   - CLI: `${CLAUDE_PLUGIN_ROOT}/skills/agent-interface-design/references/cli/checks.md` and `${CLAUDE_SKILL_DIR}/references/cli-audit-workflow.md`; MCP: `${CLAUDE_PLUGIN_ROOT}/skills/agent-interface-design/references/mcp/hard-rules.md` and `${CLAUDE_SKILL_DIR}/references/mcp-audit-workflow.md`,
   - `${CLAUDE_SKILL_DIR}/references/scoring.md` and `${CLAUDE_SKILL_DIR}/references/report.md`.

   Every finding cites a probe output, a `path:line`, or is labelled an assumption.
4. **Report**, as your final message, in this order: header (target, kind, date); **scorecard** (the eight contract dimensions, each a score or `not measured`, and the overall score = the lowest dimension rounded down to 5, per scoring.md); findings most severe first (Critical / High / Medium / Low in agent terms, each with evidence, impact, fix, how to verify); what was run (the probe's commands verbatim); what was not run and why; assumptions; next step. Close with one line saying the probe output is the evidence and the target must not be run again by hand (the next run goes through `agentic-maker probe`).

A fix is a separate, explicit step in the main conversation, verified by running the same probe again.
