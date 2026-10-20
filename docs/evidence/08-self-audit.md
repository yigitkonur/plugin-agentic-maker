# Evidence, ledger row 8: the plugin audits itself, and three different projects

Recorded 2026-10-20 on Claude Code 2.1.302 (subscription login), macOS, Python 3.14 and the system 3.9. Every model run below was a fresh `claude -p` in the verified clean-room recipe (`--restricted --strict-mcp-config --plugin-dir <this repo>`, an allowlist of tools, `--permission-mode dontAsk`, a turn cap and a budget ceiling). Numbers are copied from the stream records of those runs.

## 1. The plugin audits its own CLI

`/agentic-maker:audit <repo>/bin/agentic-maker`, a forked skill, twice: before and after a first round of fixes.

| | Run 1 | Run 2 (after the first fixes) |
|---|---|---|
| Tool calls / denials / cost | 27 / 0 / $0.53 | 28 / 0 / $0.67 |
| Overall score (lowest dimension, rounded down to 5) | 70 | 85 |
| Worst finding | High: `run --prepare --workspace-dir DIR` empties any directory, `--dry-run` does not stop it | none above Medium |
| Findings | 12 (1 High, 5 Medium, 6 Low) plus a false positive of the probe itself | 7 Medium, 10 Low |

The report is a lead, not a verdict, so each finding was checked before anything was changed.

**The High finding was real.** Reproduced before the fix: a directory holding `important.txt`, then `run release-notes --prepare --dry-run --workspace-dir <that directory>`. The directory afterwards held only the seeded fixtures; `important.txt` was gone. After the fix the same call is refused:

```
error [conflict/workspace_dir_not_ours]: .../precious is not empty and was not made by `run --prepare`; it would be emptied    (exit 5, important.txt still there)
error [usage/prepare_has_no_dry_run]: --prepare writes a scratch workspace and a take directory, so --dry-run cannot preview it    (exit 2)
error [validation/workspace_dir_unsafe]: refusing to empty /Users/.../plugins: it holds your home directory or this project    (exit 6)
```

A new directory and a second `--prepare` of the same directory (it carries a marker file) both work (exit 0). `scripts/check.sh` now fails if a `--prepare` ever touches a directory it did not make.

What else the audit found, and what was done (verified by running the command again, not by rereading the diff):

| Finding | Verified how | Result |
|---|---|---|
| bare `agentic-maker --json` printed help and exited 0 | seen in the probe's own rows (`json.pure`, `exit` findings) | now a usage error envelope, exit 2, checked piped and with `--json` (help only on a terminal) |
| `ledger gate --help` printed nothing; `gate` reads stdin until EOF | the missing help was seen in the probe rows; the hang was inferred by the audit, not observed | help works; on an open, silent pipe the gate now returns after 2.2 s with exit 0 (measured), so a hook cannot hang. `scripts/check.sh` guards it |
| `destructive.no_bypass` fired on the word "remove" in a help paragraph | probed the CLI | destructiveness is judged on the top-level command list only; a skipped destructive command's own help is reported as unverified |
| help pages without examples (`probe`, `check`, `ledger` and the ledger actions) | probed every subcommand | every subcommand has an example; the probe reports 0 findings on the CLI |
| `next_actions` value `trace-reader on <path>` is not a command | read the envelope | `{"delegate": "trace-reader", "input": ...}`; commands that still hold a `<placeholder>` carry `"template": true` |
| `--env K=V` of `probe mcp` puts a secret on the command line | read the code | `--env NAME` passes your own value on; unset names fail with a hint |
| `ledger init` accepted any session id and overwrote an existing run id | read in the code | session ids are `[A-Za-z0-9_-]` (`../../etc` is refused); an existing run id is refused (exit 5) |
| `eval-emit` left stale graders after a receipt was removed | read in the code | it deletes the graders it wrote earlier (emitted two receipts, removed one, emitted again: `receipt-2-exists.md` gone) |
| `project root` help claimed a walk-up the code did not have | ran a command from a subdirectory | the root is now the nearest ancestor with `.agentic-maker`, else `.git`/`.claude-plugin` |
| `probe cli` hid stdout/stderr of declared commands, cropped `--sub` help, suggested `check --json` (fails alone with exit 2) | saw it in the probe output | `runs[]` with exit, timing and 160-character heads; a named `--sub` returns its own help; suggestions exclude commands whose usage line needs an argument (checked on this CLI and on a clap CLI) |
| `check receipts` passed with zero receipts; `check predicate` failed with zero predicates | ran both | zero receipts is partial (exit 8, "nothing was checked"); zero predicates is ok with a warning; `check receipts --list` prints what would run without running it |
| partial results looked like success to a reader keying on `ok` | read the envelope | partial envelopes carry `"status": "partial"` and a `reason`; documented in every `--help` |
| the launcher did not follow symlinks | linked it onto another path | follows them |

Left as they are, on purpose, and reported: `ok: true` with exit 8 for partial (documented, plus `status`); the probe repeats about 3 KB of top-level help in every reply; Ctrl-C and a closed stdout pipe are not specially handled beyond an error envelope for Ctrl-C; `scan` and `detect --kind` overlap (the help now says how they differ).

The model audit was not rerun after the second round: the checks above are deterministic and were rerun, and each audit run finds a fresh handful of Lows, so a third run would not show convergence.

## 2. The audit skill's own text, found by running it

The first walkthrough audits ended after two or three tool calls with a report that had no scorecard and had not read `scoring.md` or `report.md`: the rubric was behind a link and the step said "with scoring.md and report.md". Two runs on two different projects, the same drift (S4/C4: a reference never read). The controlling text was rewritten, not added to: steps 3 and 4 of `skills/audit/SKILL.md` are now imperative `Read` calls with absolute `${CLAUDE_PLUGIN_ROOT}` / `${CLAUDE_SKILL_DIR}` paths, and the report order (scorecard first) is stated in the skill itself.

| | Before | After |
|---|---|---|
| Rust CLI: tool calls, rubric files read, scorecard | 2, 0, none | 7, 5 (contract, checks, workflow, scoring, report), yes (overall 80) |
| Python MCP server: tool calls, rubric files read, scorecard | 3, 0, none | 9, 5, yes (overall 80), and it ran `--call get_tickets={}` |

## 3. Three different projects

Created for this check in a scratch directory; none is a fixture of this repository.

### A. A Rust CLI (clap 4.6.7, built with `cargo build`)

`notes list [--json] | show <id> | delete <id>`; errors go to stdout with exit 1; no examples, no exit-code docs.

- `agentic-maker detect .` -> `cli/rust` "clap binary", and the next action names the binary the probe needs (`target/debug/rustcli`, not the crate name); on an unbuilt copy it says `cargo build` first.
- First `probe cli`: a High false positive, "no machine-readable output", because clap keeps `--json` on the subcommand and the probe read only the top-level help. Fixed: the probe reads `--help` of the listed subcommands that do not sound destructive (never `delete`), in addition to any you name. Same binary after: `list` and `show` read, no false positive.
- With `--safe 'list --json' --safe 'show 99 # expect-exit 3'`: the exit-code defect is found ("`show 99 -> exit 1`, expected 3"), plus no examples, no exit codes, and `delete` with no `--yes` and no `--dry-run` (flagged unverified: `delete --help` is never run unless you name it with `--sub`). 7 commands executed (`--help`, `--version`, the invalid command, `list --help`, `show --help`, `list --json`, `show 99`), none destructive.
- Suggestions are right: `list` is suggested, `show` is listed as needing an argument.

### B. A Python MCP server on the real `mcp` SDK (2.x)

Three tools: two with the description "Tickets.", one destructive without annotations, a `print` to stdout, an error that says "bad".

- `detect` -> `mcp/python`; `scan mcp` finds the three `@mcp.tool()` registrations and the stdout `print`.
- The first probe failed: my server used the 1.x import and mcp 2.x removed it. The probe returned `server_exited` with the server's own stderr, including the SDK's migration message. That error was marked retryable with no suggestion; now it is not retryable and says to read `details.stderr`.
- After porting the server: 3 tools, 269 estimated tokens. Findings: no annotations, unmarked destructive tool (High), identical descriptions (M7), the verbs. Two gaps showed up and were closed: identical descriptions shorter than 12 characters were not clustered, and nothing flagged a description under 25 characters. With `--call 'get_ticket={"id":99}'` the tool answered `Error executing tool get_ticket`, which the probe did not flag; it now reports `response.error_does_not_teach`.
- The audit skill's report additionally found, from reading the source, the stdout `print`, the `str(None)` returned for a missing delete, and `repr` strings instead of JSON.

### C. A bash script plus a skill, in one repo (`scripts/sync.sh`, `skills/sync-notes`)

The skill says "Reconciles divergent note repositories using bidirectional delta propagation" and "Run `scripts/sync.sh`"; the script copies one way and ignores its arguments.

- `detect` -> `cli/shell scripts/sync.sh` and `skill sync-notes`.
- `probe cli scripts/sync.sh`: nothing is run ("the script neither mentions --help nor reads its arguments, so running it would just run it"), a High `help.unknown`, and the sentinel the script would write (`/tmp/am-walk-sync-ran`) does not exist afterwards.
- `/agentic-maker:derail skills/sync-notes --rounds 3` with one scenario ("My notes are in ./notes and my backup folder ./backup is out of date. Can you bring the backup up to date with my notes?"), in a git copy, orchestrator in the clean-room recipe. 41 Bash calls, 5 reader spawns, 5 worker takes in 3 rounds, orchestrator cost $1.61, workers $0.21, ledger closed `clean`.

| Take | Receipts | What the reader and the orchestrator found |
|---|---|---|
| 1 | **4/4** | the skill was never used; the worker hand-copied. Receipts passed, the behaviour was wrong (T1) |
| 2 | 2/4 | the worker rejected the skill from its description ("two-way reconciliation; you asked for a one-way update") and stopped to ask |
| 3 | 4/4 | skill used, but the worker looked for `scripts/sync.sh` inside the skill folder and hand-copied |
| 4, 5 | 4/4, 4/4 | skill used, `bash scripts/sync.sh` ran, no denials; the reader found no drift |

```diff
-description: Reconciles divergent note repositories using bidirectional delta propagation.
+description: Brings the ./backup folder up to date with ./notes by copying notes into backup, one way. Notes is never modified, and backup is created if it does not exist. Use when the user asks to back up, sync or refresh their notes.
-1. Run `scripts/sync.sh`.
+1. From the directory that contains `notes/` (the user's working directory, not this skill's folder), run `bash scripts/sync.sh`.
```

The orchestrator rejected one reader finding after checking the disk (the script did exist at the workspace root), reversed that call when take 3 showed the path had no anchor, marked one `[NICE]` line as superseded rather than restoring it, and listed what it left open: the empty reference stubs (no worker read them), the script's hidden `cp` errors, one scenario only. The only denied call was its closing `git diff`: the skill's allowed-tools did not cover it. Fixed: `Bash(git diff *)` is allowed and the step says `git diff -- <target>`.

Not tested headlessly: proposing scenarios when none exist (the skill asks the user to approve them; the scenario here was written by hand).

## 4. The `design` skill

A first smoke (`/agentic-maker:design a command line tool that lets an AI agent manage my calendar events`, Read/Grep/Glob only) ended with 0 turns and no output: the skill's `!` injection calls the CLI by its absolute path, but `allowed-tools` listed only `Bash(agentic-maker *)`, and an injected command the permissions do not cover aborts the whole invocation silently. `audit` and `derail` already listed both forms. Fixed, and `scripts/check.sh` now fails for any skill that injects the CLI by absolute path without covering it.

Second run: 6 reads (surface choice, interview, contract, CLI deliverables, companion routing, the dated MCP-vs-CLI file), $0.15, no denials. It chose a CLI with the condition "only if you are one person on your own machine", labelled each claim as documented fact, benchmark or practitioner report, flagged the dated figures ("6 months old, verify before citing"), and opened the interview with group 1 of 4 (intent, consumer, underlying service), promising no code before approval. The remaining groups need a person; they were not run.

## 5. The final regression of the loop, with the final code

After the last code change the whole `derail` loop was run once more on a fresh copy of the seeded skill from `docs/evidence/04-derail-loop.md` (`/agentic-maker:derail skills/manifest-synth --rounds 3`, one scenario, two takes a round, budget $3, clean-room recipe).

| | Before the edit (round 1) | After the edit (round 2) |
|---|---|---|
| Receipts | take 1: 7/11, take 2: 10/11 | take 1: 11/11, take 2: 11/11 |
| Skill used | 1 of 2 takes | 2 of 2 |
| Ledger | closed `clean` after 2 of the 3 approved rounds; workers $0.14, whole session $1.64 | |

The edit rewrote the jargon description into a user's words and replaced `reference/format.md` and the unanchored `scripts/group.py` by paths relative to the skill's base directory. The report names what it left open: one skill-trigger sample of two, two title predicates that cannot match a JSON-escaped argument (judged from the trace, not edited), a vague "keep each entry short" next to a 72-character rule it left alone for lack of evidence.

The run found two more defects in the plugin's own text, both fixed:
- **The reader's first output failed verification in both takes** ("none of 4 findings verified"): the reader's prompt pointed at `derailment-method/references/finding-schema.md`, a relative path it could not resolve, so it guessed the shape. The JSON skeleton and the allowed predicate types are now in `agents/trace-reader.md` itself. Reader-only check on a recorded trace: the first output has the right shape, and the checker verified the one finding whose quote was exact and rejected the two whose quotes were not (the gate doing its job). With the wrong project root the same file is rejected for a missing controlling file, which is why `check findings` resolves them against `--root`.
- **The closing `git diff` was denied again**, this time as `git -C <dir> diff`. `allowed-tools` now covers both forms.

Seen and left alone: the reader, under `--restricted`, tried to open the worker's output file in its temporary workspace, which is outside the directories the orchestrator was given; it fell back to `receipts.json`. This is a property of the clean-room recipe, not of the skill text.

## 6. Footprint and `eval-emit`

- `claude plugin details agentic-maker` on a temporary-config install of this repo: **Always-on ~309 tok** (design 40, derail 40, derailment-method 60, audit 40, agent-interface-design 80, trace-reader 50); on-invoke 540 to 2k. `scripts/check.sh` fails above 400.
- `eval-emit` converts the fixture scenario into a `claude plugin eval` case, and `check.sh` converts it on every change. The emitted case was also run for real: written into the wrapper plugin of a `run --prepare` of the seeded skill, then `claude plugin eval <wrapper> --scaffold --case release-notes --runs 1 --trust-plugin` (2.1.304, 25 s, $0.10). With the plugin the score was 0.67 (the file exists and the `## Features` heading matches; the title regex fails and the skill did not fire); without it 0.33; delta +0.33. Four graders were emitted (file exists, two regexes, skill fired); 8 of the scenario's 11 receipts (commands, exact counts, unchanged files, mtime window, no extra files) cannot be expressed as eval graders and are listed in the emit result instead of being dropped silently.

## Limits

- Every model run is one sample; the agent is not deterministic. The before/after of section 2 is two runs against three, not a rate.
- The projects in section 3 are small and written for this check. They show that the detection, the probes and the loop work on three stacks and that the first breaks the plan predicted (a binary path that is not the crate name, a script that ignores its arguments, a server that needs its own virtualenv) are handled; they do not show recall on real-world tools.
- `UNVERIFIED`: the rest of the `design` interview; the model-level self-audit after the last round of fixes; Windows.
