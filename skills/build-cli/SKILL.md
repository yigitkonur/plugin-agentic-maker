---
name: build-cli
description: Build or repair an agent-facing CLI, probe it, hand over the test. Started by you.
disable-model-invocation: true
argument-hint: "<what the CLI should do | path of a CLI to repair>"
allowed-tools: Bash(agentic-maker *) Bash(${CLAUDE_PLUGIN_ROOT}/bin/agentic-maker *) Read Grep Glob Write Edit
---

# Build a CLI for agents

Request: `$ARGUMENTS`

The caller is an AI agent in a shell. It reads stdout, trusts the exit code, cannot answer a prompt, and learns the tool from `--help`. Pages are under `${CLAUDE_PLUGIN_ROOT}/skills/agent-interface-design/references/cli/`; open one when the step names it. This runs in the main conversation: ask the user directly, and only what changes the result.

## Pick the mode

| The request is | Do |
|---|---|
| a new CLI | steps 1-6 |
| a path to an existing CLI (relative to the current working directory, not to the plugin) | `ls` it, run the baseline probe from step 4 first and read its findings, then steps 3-6 on what they found |
| one more command for an existing CLI | step 2 for that command, then 3-6 |

## Steps

1. **Scope.** The task the agent will do, who runs it, and which operations change or delete things. If the idea is still vague, ask the CLI interview in [interview-cli.md](../design/references/interview-cli.md) one group at a time and write the sketch down first ([cli-deliverables.md](../design/references/cli-deliverables.md)); code starts after the user agrees to it.
2. **Ground it.** Facts about what the CLI wraps (an API, a file format, another command) come from the real thing: its docs, its `--help`, real output. Every command, flag and path you put in its help comes from there; one found nowhere goes in the report as a suggestion. A CLI written from memory of an API repeats the memory's mistakes. If the `research` plugin is installed use `/research:ask`; if you can verify nothing, say so. A language-specific builder skill is named only if it is installed ([companion-routing.md](../agent-interface-design/references/decisions/companion-routing.md)).
3. **Build in this order, one stage at a time.** Do not start a stage before the probe in step 4 is clean for the one before. [repair-build-order.md](../agent-interface-design/references/cli/repair-build-order.md) has the order and the envelope:
   1. Stdout is data only, `--json` gives one JSON object, logs and progress go to stderr ([streams-and-jsonl.md](../agent-interface-design/references/cli/streams-and-jsonl.md)).
   2. Errors carry class, code, message, `retryable` and a suggestion; exit codes tell usage, not-found, auth and transient apart ([envelope-and-errors.md](../agent-interface-design/references/cli/envelope-and-errors.md), [exit-codes.md](../agent-interface-design/references/cli/exit-codes.md)).
   3. It never blocks: no prompt, `--yes` or `--dry-run` on everything that changes or deletes ([non-interactive.md](../agent-interface-design/references/cli/non-interactive.md), [dry-run.md](../agent-interface-design/references/cli/dry-run.md)).
   4. Where the agent must repair and resubmit something, say what to change in the error ([iterative-repair.md](../agent-interface-design/references/cli/iterative-repair.md)).
   5. `--help` with examples, exit codes and the output shape, per command ([discovery-and-help.md](../agent-interface-design/references/cli/discovery-and-help.md)).
   6. Long operations: jobs or JSONL only if needed ([async-and-long-running.md](../agent-interface-design/references/cli/async-and-long-running.md)).
4. **Probe after each stage.** Run each check as its own Bash call, with no `&&`, `;` or heredoc; a denied call skips only that check, and Read, Grep and Glob are the fallback. `agentic-maker probe cli <binary> --safe "<read-only args>" --safe "<read-only args>"` runs the CLI the way an agent would and changes nothing. Never put a command that creates, updates, deletes or sends in `--safe`, not even with a dry-run flag: whether the flag is honoured is what you are checking. Each finding names the page that holds the fix. Fix, probe again, stop when no High finding is left.
5. **Hand over the test.** Only the user can start `/agentic-maker:derail`; you cannot, so do not try. Write three scenarios into `.agentic-maker/scenarios/<name>.md` (format in `${CLAUDE_PLUGIN_ROOT}/skills/derail/references/scenarios.md`, `kind: cli`, `bin:` the binary): a normal task, a task whose first attempt fails (wrong id, missing auth), and one that tempts the agent to a destructive command. Receipts run your probe on the result and check the disk, not the agent's words. Preview one with `agentic-maker run <name> --dry-run`, and end by giving the user the exact command `/agentic-maker:derail <binary>`. Until they run it the CLI is untested, and your report says so.
6. **Ship.** The final message is a table with one row per finish criterion in [checks.md](../agent-interface-design/references/cli/checks.md), marked checked (the command and its output, or the file and line you read) or unchecked, followed by what you probed and what you handed over. A message without that table is not a ship.

## Do this, not that

| Do | Not |
|---|---|
| Probe after every stage | Build all six stages, then probe once |
| Fix the sentence or code that misled the agent | Add a "do not" note beside it |
| Put a secret in an environment variable or a file | Take it as an argument |
| Say what you could not verify | Present a guess as a fact |
