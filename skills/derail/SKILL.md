---
name: derail
description: Test a skill, plugin, CLI or MCP tool with fresh agents, read their runs, fix the text that caused each drift, rerun. Started by you; spends model usage.
disable-model-invocation: true
argument-hint: "<target path or scenario> [--rounds N] [--runner headless|existing] [--from <record>]"
allowed-tools: Bash(agentic-maker *) Bash(${CLAUDE_PLUGIN_ROOT}/bin/agentic-maker *) Bash(git diff *) Bash(git -C * diff *)
hooks:
  Stop:
    - hooks:
        - type: command
          command: "${CLAUDE_PLUGIN_ROOT}/bin/agentic-maker ledger gate"
---

<!-- src: audit-skill-by-derailment/SKILL.md#When to Use -->
# Derail

Arguments: `$ARGUMENTS`

Environment: !`${CLAUDE_PLUGIN_ROOT}/bin/agentic-maker doctor --human 2>&1 || true`

Use this when you want to know whether a skill (or plugin, CLI, script or MCP tool) holds up when an autonomous agent uses it for a real task, why an agent drifted, guessed or stopped early, or whether a fix closed the drift it was meant to close. Do not use it to create a skill from nothing, to rewrite a one-off prompt, or for copy edits that would not change what an agent does.

Method and vocabulary come from the `derailment-method` skill (invariants, markers, the root-cause codes, fix patterns). Read it before judging anything.

## The loop

Work serially through these steps. Every step ends in a command whose output you read; a claim is not a result.

**How to run the commands:** one `agentic-maker` command per Bash call, with literal paths copied from the previous reply (every reply carries the next command in `next_actions`). Shell variables, `&&` or `;` chains and heredocs cannot be checked against the allowed-tools patterns and are denied. A scenario can be named instead of pathed: `agentic-maker run release-notes`.

1. **Frame.**
   - The target is in the arguments. If it is not, or you cannot tell its kind (`skill`, `plugin`, `cli`, `mcp`), ask the user once.
   - Scenarios are files in `.agentic-maker/scenarios/`. If there are none for this target, propose three (a normal task, an ambiguous one, a failure-injection one) following [scenarios](references/scenarios.md), and write them once the user agrees. **A scenario prompt must read like a user's request and must never name the target.**
   - Preview the cost: `agentic-maker run <scenario> --dry-run` for each scenario. Show runner, model, turn cap, budget ceiling and the number of takes, then ask before spending.
   - Open the ledger: `agentic-maker ledger init --session ${CLAUDE_SESSION_ID} --target <the target directory, exactly as given in the arguments> --budget-usd <n>`. (Files a fix later touches are added automatically.)
2. **Run.** `agentic-maker run <scenario> --session ${CLAUDE_SESSION_ID}` starts a fresh worker in a clean room and keeps everything. Several takes of the same scenario are normal (agents are not deterministic). Long runs: start them with the Bash tool in the background and wait for the completion notice; do not poll. Runner choices: [runners](#runners).
3. **Receipts.** `agentic-maker check receipts <take>`. A run whose receipts fail is not a success, whatever the worker said.
4. **Read.** Spawn the `trace-reader` agent once per take (at most five at a time) with absolute paths to `trace.md`, `trace.norm.jsonl`, `receipts.json`, `env.json`, the target files and the scenario prompt. It is read-only and returns one JSON object as its final message. It runs in the background: wait for its completion notice, and do not `sleep` or poll. Save the reply with the Write tool as `<take>/findings/<n>.json`.
5. **Verify.** `agentic-maker check findings <file> --trace <take>/trace.norm.jsonl --out <take>/findings/verified.json`. A rejected finding (quote not verbatim, event missing, bad code) is dropped or sent back to the reader; **never fix an unverified finding**.
6. **Synthesize.** Merge findings across takes and scenarios, rank by severity, apply the compound-P0 rule. See [synthesis-matrix](references/synthesis-matrix.md).
7. **Fix the cause.** `agentic-maker ledger fix <ids> --session ${CLAUDE_SESSION_ID} --findings <file> --trace <norm>`, then rewrite or delete the controlling text named in the finding (patterns: `derailment-method/references/fix-patterns.md`). You are the only writer. After each edit run `agentic-maker check diff --findings <file> --finding <id>` (it flags an edit that only adds a rule beside unchanged cause text) and `agentic-maker check nice --findings <file>`.
8. **Rerun** in a fresh session: run the scenario again, then `agentic-maker check predicate --findings <file> --trace <new take>/trace.norm.jsonl`. The finding is closed only when its predicate passes and the receipts pass. A predicate that is "not met" while the trace plainly shows the behaviour is a badly written predicate (it tested a command's exact wording): say so in the report, judge it from the trace, and do not edit it to pass.
9. **Stop** when there is no P0 or P1, the receipts pass and two consecutive takes are clean; or when the round limit (default 5) or the budget is reached. Then `agentic-maker ledger close --session ${CLAUDE_SESSION_ID} --outcome clean|open|unverified --reason "<why>"`. Report the rounds, the text that changed (`git diff -- <target>`, run from the project directory), the evidence references, and everything left open or unverified.

## Rules

- **Before you ask the user a question mid-loop**, run `agentic-maker ledger set-status awaiting_user --session ${CLAUDE_SESSION_ID}`; the Stop gate otherwise treats an edited target with no fresh run as "about to claim fixed" and blocks. Set it back with `running` when you continue.
- If a fix cannot be re-tested (no budget, no access), close with `--outcome unverified` and say so; do not report it fixed.
- A harness restriction that stops the worker from reading the skill's own files is a defect of the run (O6), not of the skill. Check `env.json` and the permission denials in the trace before blaming the text.
- Do not edit scenario Receipts to make a run pass.
- No errata files, no mistake notebooks: the corrected source is the deliverable.

<!-- src: audit-skill-by-derailment/SKILL.md#Tri-Modal Routing Decision Tree -->
## Runners

```
How is the target being evaluated?
|- a fresh agent on a realistic task, cheap, repeatable ......... runners/headless.md   (default)
|- a session you already ran (any harness, any source) ........... runners/existing.md
`- a live interactive agent: dialogs, approvals, multi-turn ...... runners/herdr.md     (follow herdr-conductor)
```

<!-- src: audit-skill-by-derailment/SKILL.md#Available Scripts -->
## Commands (`agentic-maker`, on PATH while the plugin is enabled)

| Command | Purpose |
|---|---|
| `run <scenario> [--dry-run] [--runner headless\|existing --from <record>] [--session id]` | start a fresh worker (or ingest a record) and keep the trace, env report and workspace |
| `normalize <take or file>` | trace.norm.jsonl and trace.md from stream-json or a session transcript |
| `check receipts <take>` | what the run left on disk, against the scenario's Receipts |
| `check findings <file> --trace <norm>` | every quote verbatim in the cited events |
| `check diff / nice / predicate` | the applied edit fixed the cause / a [NICE] line survived / the rerun passed |
| `ledger init / fix / set-status / close / abandon / status` | the loop's state; survives compaction; backs the Stop gate |

Each command has `--help` with examples and its exit codes (0 ok, 2 usage, 3 not found, 6 validation, 8 partial).

<!-- src: audit-skill-by-derailment/SKILL.md#Reference Routing -->
## Read when

| File | Read when |
|---|---|
| [references/scenarios.md](references/scenarios.md) | writing or proposing scenarios and receipts |
| [references/clean-room.md](references/clean-room.md) | deciding isolation, or a run looks contaminated |
| [references/runners/headless.md](references/runners/headless.md) | the default runner, its flags, its limits |
| [references/runners/existing.md](references/runners/existing.md) | auditing sessions that already happened |
| [references/runners/herdr.md](references/runners/herdr.md) | a live round under herdr |
| [references/trace-sources.md](references/trace-sources.md) | choosing what record to read; what `Ctrl+O` does |
| [references/synthesis-matrix.md](references/synthesis-matrix.md) | merging findings across takes, scenarios, repos |
| [references/targets/](references/targets/skill.md) | target-specific scenarios and lenses: skill, plugin, cli, mcp |
