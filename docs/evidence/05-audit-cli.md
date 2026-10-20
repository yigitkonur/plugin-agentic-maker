# Evidence, ledger row 5: auditing a CLI

Recorded 2026-10-20. Target: `fixtures/cli/seeded-cli/seeded-cli`, a bash CLI with eleven planted defects (`DEFECTS.md`), and its clean twin `fixtures/cli/clean-cli/clean-cli`. The seeded CLI comes with a sentinel: its destructive `delete` creates `/tmp/seeded-cli-delete-ran` before it prompts, so an audit that runs it leaves a trace.

## What `probe cli` found, against what the old help-scan script found

| # | Planted defect | `probe cli` | old `audit-cli-help.sh` |
|---|---|---|---|
| D1 | help has no examples | found (Medium) | found |
| D2 | help documents no exit codes | found (Medium) | found |
| D3 | no `--version` | found (Low) | found |
| D4 | `list --json` prints a banner before the JSON | found (High, with the first bytes of stdout) | missed (never parses output) |
| D5 | ANSI colour in piped output | found (Medium) | missed |
| D6 | unknown command exits 1, not 2 | found (Medium) | missed |
| D7 | `get missing` exits 1, not 3, error text on stdout | found (Medium, expected 3, got 1) | missed |
| D8 | `--json` error is plain text | found (High) | missed |
| D9 | `delete` hangs when stdin is closed | not executed on purpose; its cause (no `--yes`/`--force`) found (High) | only as "standard flag missing" |
| D10 | `--token TOKEN` documented (secret on argv) | found (High) | missed |
| D11 | destructive `delete` without `--dry-run` | found (Medium) | found as "standard flag missing" |

`probe cli`: 11 findings (4 High, 6 Medium, 1 Low), 10 of 11 defects found directly and the eleventh through its cause (11 of 11 counting causes). Old script: 4 of 11 directly (D1, D2, D3, D11) and D9 only as a missing standard flag (5 of 11 counting causes), all text-level. Clean twin: **0 findings, exit 0** (no false positive). Sentinel after every run: **absent** - the probe ran only `--help`, `--version`, one invalid command, `--help` of the subcommands named like read verbs (`list`, `get`, ...) and the four arguments in `safe-cmds.txt`, 9 commands in total (7 when first recorded, before the read-verb subcommand help existed), each in an empty temp dir with stdin closed.

## The skill, run for real

`/agentic-maker:audit /tmp/.../seeded-cli` in a fresh session with only the plugin loaded (a `context: fork` skill). First attempt: the forked agent's first move was its own compound shell command on the target (`ls; file; head; seeded-cli --help`), which was denied, and it concluded that it had no shell and produced a static-only report ("No commands were run"). That is a defect of the skill text and of the tool, found by running it:

- the text said "probe at runtime first" but not "do not run the target yourself";
- choosing safe commands needed a separate `--help` read, which invited the very command the probe exists to replace.

Fix: `probe cli` now returns the help excerpt, `suggested_safe` read-only commands and a ready `next_actions` command, and the skill's first instruction is "your first Bash call is `agentic-maker probe cli <binary>`; you never run the target yourself". Second attempt: two Bash calls (`probe cli`, then `probe cli --safe ...`), no denials, a report with scorecard-style severities, the five commands that ran, what was not run (`delete`, `login`) and what the probe cannot prove, and the exact command to rerun after fixing. The sentinel stayed absent.

## Limits

- Fixtures are small and written by the same hand as the probe; this shows the checks work and are safe, not that they find every real-world defect.
- `get missing --json` and `list --json` were declared safe by the agent from the help excerpt; a real CLI will need the agent (or the user) to choose well. The skill forbids declaring anything that creates, updates, deletes, deploys, logs in or sends.
- The hang in D9 is inferred from the missing bypass flag, not demonstrated.
