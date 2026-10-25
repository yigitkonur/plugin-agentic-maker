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
| a path to an existing CLI (relative to the current working directory, not to the plugin; Read, Edit and Write need `<pwd>/<path>` built from the output of `pwd`, never a guessed prefix) | `ls` it, run the baseline probe from step 4 first and read its findings, then steps 3-6 on what they found. No Write or Edit comes before those baseline findings are read; after that the existing file changes only with Edit, one stage per Edit, never with a Write over the whole file. Keep what each command does and the fields it prints; a stage that changes an output shape (a bare array into an object) goes under "Behaviour changes" in the report |
| one more command for an existing CLI | step 2 for that command, then 3-6 |

## Steps

1. **Scope.** The task the agent will do, who runs it, and which operations change or delete things. If the idea is still vague, ask the CLI interview in [interview-cli.md](../design/references/interview-cli.md) one group at a time and write the sketch down first ([cli-deliverables.md](../design/references/cli-deliverables.md)); code starts after the user agrees to it.
2. **Ground it.** Facts about what the CLI wraps (an API, a file format, another command) come from the real thing: its docs, its `--help`, real output. Every command, flag and path you put in its help comes from there; one found nowhere goes in the report as a suggestion. A CLI written from memory of an API repeats the memory's mistakes. If the `research` plugin is installed use `/research:ask`; if you can verify nothing, say so. A language-specific builder skill is named only if it is installed ([companion-routing.md](../agent-interface-design/references/decisions/companion-routing.md)).
3. **Build in this order, one stage at a time, probing after each.** For each stage below: open the page it names, Write or Edit only what that stage needs, run the probe of step 4, and fix its High findings before the next stage opens. The first Write of a new CLI holds stage 1 only; each later stage is one Edit followed by one probe call, so code for two stages in one Write or Edit means the probe between them was skipped. Where the spec is silent, follow the pages and list the choice in the report. [repair-build-order.md](../agent-interface-design/references/cli/repair-build-order.md) has the order and the envelope:
   1. Stdout is data only, `--json` gives one JSON object, logs and progress go to stderr ([streams-and-jsonl.md](../agent-interface-design/references/cli/streams-and-jsonl.md)).
   2. Errors carry class, code, message, `retryable` and a suggestion; exit codes tell usage, not-found, auth and transient apart: 2 only for a malformed command line (unknown command or option, missing argument); an id or name that matches no item, a non-numeric one included, is not-found (3) ([envelope-and-errors.md](../agent-interface-design/references/cli/envelope-and-errors.md), [exit-codes.md](../agent-interface-design/references/cli/exit-codes.md), [error-classes.md](../agent-interface-design/references/cli/error-classes.md)).
   3. A secret is read from an environment variable or a file, never from an argument: no `--token VALUE` form in any help page, top-level or per command. If existing callers need the old flag, the parser may still accept it silently and the report lists that under "Behaviour changes" ([auth-and-secrets.md](../agent-interface-design/references/cli/auth-and-secrets.md)).
   4. It never blocks: no prompt, `--yes` or `--dry-run` on everything that changes or deletes ([non-interactive.md](../agent-interface-design/references/cli/non-interactive.md), [dry-run.md](../agent-interface-design/references/cli/dry-run.md)).
   5. Where the agent must repair and resubmit something, say what to change in the error ([iterative-repair.md](../agent-interface-design/references/cli/iterative-repair.md)).
   6. `--help` with examples, exit codes and the output shape, per command ([discovery-and-help.md](../agent-interface-design/references/cli/discovery-and-help.md)).
   7. Long operations: jobs or JSONL only if needed ([async-and-long-running.md](../agent-interface-design/references/cli/async-and-long-running.md)).
4. **Probe after each stage.** Run each check as its own Bash call, with no `&&`, `;`, `cd`, `echo $?` or heredoc (`pwd` and `ls` too, and files change with Edit, never `sed`): a non-zero exit already shows as `Exit code N` in the result; a denied call skips only that check, and Read, Grep and Glob are the fallback. `agentic-maker probe cli <binary> --safe "list --json" --safe "get 1 --json # expect-exit 0"` runs the CLI the way an agent would and changes nothing; each `--safe` is a real read-only command of this CLI, because the probe runs `--help`, `--version` and a bad command by itself. Never put a command that creates, updates, deletes or sends in `--safe`, not even with a dry-run flag: whether the flag is honoured is what you are checking. Nor with a missing-confirmation flag you expect it to refuse: if the guard fails, the probe has already changed something, so check a refusal as its own Bash call. A command the request forbids running is run in no form, `--dry-run` included: read its code and mark it unchecked in the ship table. Any other such command is run once with `--dry-run` as its own call, then `ls` shows that nothing changed, and its real write path stays unchecked in the ship table. Each finding names the page that holds the fix. Fix, probe again, read the whole `findings` list of each probe result (never pipe it through head, tail or grep) and stop only when you have seen it and it has no High entry; a probe result you did not see leaves that criterion unchecked.
5. **Hand over the test.** Only the user can start `/agentic-maker:derail`; you cannot, so do not try. Create three scenario files with the Write tool, one call per file at `.agentic-maker/scenarios/<name>.md`; Write makes the folder, so no `mkdir` or heredoc. The format is in `${CLAUDE_PLUGIN_ROOT}/skills/derail/references/scenarios.md`: front matter `kind: cli` with both `target:` and `bin:` set to the binary, and every Receipts line starting with `- `. The scenarios are: a normal task, a task whose first attempt fails (wrong id, missing auth), and one that tempts the agent to a destructive command. Receipts run your probe on the result and check the disk, not the agent's words. Preview all three with `agentic-maker run <name> --dry-run`, each as its own Bash call; each preview must list every receipt you wrote, and every receipt line must use a kind from the receipts table in scenarios.md. Fix a line that does not before you hand over. End by giving the user the exact command `/agentic-maker:derail <binary>`. Until they run it the CLI is untested, and your report says so.
6. **Ship.** The final message is a table with one row per finish criterion in [checks.md](../agent-interface-design/references/cli/checks.md), marked checked (a command that exercises exactly that criterion and its output, or the file and line you read) or unchecked; "not tested" or a claim with no command or file:line is unchecked. It is followed by what you probed and what you handed over. A message without that table is not a ship.

## Do this, not that

| Do | Not |
|---|---|
| Probe after every stage | Build several stages, then probe once |
| Fix the sentence or code that misled the agent | Add a "do not" note beside it |
| Say what you could not verify | Present a guess as a fact |
