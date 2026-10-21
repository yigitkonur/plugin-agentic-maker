# agentic-maker

A Claude Code plugin for **making tools that agents use well** and **testing them against real agent behaviour**.

- **Design and audit** a CLI, script, MCP server or skill against one eight-question contract, using probes that run the thing the way an agent would instead of regex over source.
- **Derail** it: start a fresh agent on a realistic task, read the whole execution, find where it drifted, rewrite the text that caused the drift (not "do / don't" rules beside it), and rerun.

It works on any project and language: the probes act on the public interface (an executable, an MCP endpoint, a skill's text), and language code lives only in reference files that are read when needed.

```
/plugin marketplace add yigitkonur/plugin-agentic-maker
/plugin install agentic-maker@plugin-agentic-maker
```

Or from a shell in one step: `claude plugin install agentic-maker --marketplace yigitkonur/plugin-agentic-maker`.

Needs `python3` 3.9+ (standard library only) and, for fresh-agent runs, `claude` on PATH. Built and tested on Claude Code 2.1.304 (`claude plugin eval`, used by `eval-emit`, needs 2.1.269 or later). `herdr` is optional (live interactive rounds, and finding a pane's session). `git` is used only by `check diff` when you do not pass `--session`; `jq` only if you want the recipes in `skills/derail/references/session-recipes.md`. Nothing else.

If you still have the three skills this plugin replaces (`audit-agentic-cli`, `audit-agentic-mcp`, `audit-skill-by-derailment`), disable them once you have read [docs/parity/REPORT.md](docs/parity/REPORT.md): they claim the same requests.

## Try it

Point it at something you have:

```
/agentic-maker:audit ./bin/mytool          # a CLI: runs --help, --version, one invalid command and the read-only commands you allow
/agentic-maker:derail skills/my-skill      # a skill: fresh agents on realistic tasks, then fixes the text that misled them
/agentic-maker:design a tool that lists and cancels our scheduled backups
```

An audit ends in a scorecard and findings, each with its evidence. This is part of a real one, on the plugin's own "clean" fixture CLI before it was fixed:

```
Overall: 75 (7 of 8 measured). Contract is the lowest measured dimension.
F1. High: unknown flags are silently accepted and the command succeeds
    Evidence: `list --bogus --json` exited 0 and returned the normal item list
    Fix: reject any unrecognised option with exit 2, class `usage`, naming the flag
    Verify: agentic-maker probe cli clean-cli --safe "list --bogus --json # expect-exit 2"
```

A derail run ends with what changed and what is still open, and refuses to say "clean" without proof. This is from a real run on one skill (3 takes, $0.12):

```
ledger: closed clean | receipts 8/11, 9/11, 11/11 | F1-F5 fixed, each with a passing verdict from a take that ran after the fix
$ agentic-maker ledger close --outcome clean      (before the rerun)
error [conflict/not_witnessed]: the loop cannot be closed as clean: 8 of 11 receipts fail in the newest take; ...#F1: no rerun-predicate verdict is recorded
  next: agentic-maker run release-notes --session ...
```

## Commands

| Command | What it does |
|---|---|
| `/agentic-maker:audit <target>` | Probes a CLI, script, MCP server or skill and reports against the contract with a scorecard and evidence. It is instructed to change nothing; it runs in a forked agent with the usual tools, so that is an instruction, not a sandbox. |
| `/agentic-maker:derail <target>` | The loop: scenarios, fresh agents in a clean room, a read-only reader whose reply a hook saves and checks, a fix of the controlling text, a rerun, and a ledger that refuses "clean" until each fix is witnessed (plus a Stop gate that refuses "fixed" without a fresh run). |
| `/agentic-maker:design <idea>` | Chooses CLI, MCP or skill, asks the interview of that surface, and sketches it before any code. |
| `agent-interface-design` (model-invoked) | Write-time guidance when an agent-facing surface is being built or reviewed; tells the model to run `agentic-maker probe` on what it built. |
| `derailment-method` (model-invoked, narrow) | The vocabulary and discipline of the method; preloaded into the reader. |

The CLI behind them is `agentic-maker` (on PATH while the plugin is enabled): `doctor`, `detect`, `scan`, `probe cli|cli-diff|mcp` (each keeps its whole reply under `.agentic-maker/runs/audit-<date>/`), `run`, `normalize` (a file, `session:<id>` or `herdr:<pane>`), `check receipts|findings|diff|predicate|nice`, `ledger init|status|fix|judge|close|abandon`, `eval-emit`. One JSON envelope on stdout when piped, diagnostics on stderr, exit codes 0-8, never a prompt. `agentic-maker <command> --help` has examples and the exit-code table.

## How a derailment run works

```
scenario (an everyday request that never names the target; receipts say what must be true afterwards)
  -> run: a fresh `claude -p` in a clean room (--restricted, only the target loaded), or a live herdr worker
  -> normalize: one trace with [n] references; nothing dropped silently
  -> receipts, checked when the take ends: what the run left on disk (the agent's own report is only a claim)
  -> trace-reader (Read/Grep/Glob only, no CLAUDE.md): findings as JSON, each with a quote, the controlling text and a rerun predicate
  -> a hook saves the reply and runs check findings: every quote must be verbatim in the cited events (one send-back if not)
  -> fix: ledger fix keeps a copy; rewrite the controlling text; check diff flags an edit that only adds a rule beside it
  -> rerun in a fresh session; check predicate records the verdict; ledger close --outcome clean is refused until it is witnessed
```

Why it is built this way, with the evidence: [docs/what-is-true.md](docs/what-is-true.md) (the questions put to a real Claude Code, U1-U16 and the findings E1-E20; most answered by running something, a few partly or not at all, and it says which), [docs/evidence/](docs/evidence/) (one file per capability, with the runs), [docs/design/](docs/design/README.md) (the plan this was built from).

## Status

Each row says what was watched on 2026-10-20 and 21 (Claude Code 2.1.302 to 2.1.304, herdr 0.9.5, macOS) and what was not. "Fixture-tested" means exercised on planted-defect fixtures that live in this repo. Model runs are single samples: the numbers are recorded in `docs/evidence/`, the stream records themselves are not kept in the repo (they hold session metadata). `scripts/check.sh` guards the probes, the findings check, the containment rules, links, manifests and footprint; the receipts, the witnessed ledger, `check diff`, predicates, the reader hook, `[NICE]` and the Stop gate were watched in the runs below, not regression-tested.

| Capability | Status | Evidence |
|---|---|---|
| Derail loop on a skill (headless, clean room) | watched working, the whole loop with no human in it | [04](docs/evidence/04-derail-loop.md) |
| Stop gate blocks a premature "fixed" | watched working in the real harness | [04](docs/evidence/04-derail-loop.md) |
| `audit` of a CLI (`probe cli`) | watched working; fixture-tested: 10 of 11 planted defects found directly, 11 counting causes (the old script: 4, or 5), clean twin silent under the default probe and under the extra probes a full audit chose (the first twin was not clean under a full audit: 6 gaps, fixed in 0.2.0) | [05](docs/evidence/05-audit-cli.md), [09](docs/evidence/09-second-review.md) |
| `audit` of an MCP server (`probe mcp`, stdio and HTTP) | watched working; budget equals a hand count | [06](docs/evidence/06-audit-mcp.md) |
| Round limit, budget ceiling and the per-fix snapshot of `check diff` | watched: `rounds_exhausted` and `budget_exhausted` (exit 5), a rule added beside an unchanged cause flagged, a rewritten cause passes | [09](docs/evidence/09-second-review.md) |
| Derail loop on a CLI and on an MCP server | watched working on the seeded fixtures, one scenario each: the reader found a harness-induced stop (O6) on the CLI and tools listed with no handler on the MCP server; fixes verified by 3/3 receipts on two reruns | [09](docs/evidence/09-second-review.md) |
| `claude plugin eval` over `evals/` | watched: 10 cases, 3 runs each, with and without the plugin (mean Δ +0.40): the five stay-quiet cases score 1.00 / 1.00; the trigger cases written in plain words fire (+1.00), except a small "write this tool's definition" question, which is answered without the skill (1 of 3) | [10](docs/evidence/10-round-two.md) |
| Live herdr round with a Claude worker | watched working, two rounds; receipts 11/11 (the first round needed an ingest fix first, the second passed at once) | [07](docs/evidence/07-live-herdr.md) |
| Ingest a Claude session transcript or `stream-json` | watched working | 04, 07 |
| Ingest a Codex rollout | matches the `jq` recipes event for event on a real recorded run (28 events); **no live Codex worker run**: Codex asked to log in again, which only the user can do | [10](docs/evidence/10-round-two.md) |
| agy | never launched by the plugin (a launch can have effects it cannot see); a session you already ran is read from its transcript by id or herdr pane (matches the recipes on a real session, 20 events) | [10](docs/evidence/10-round-two.md) |
| The ledger as witness | watched: `clean` refused until each fix has a passing verdict from a take that ran after it, an edit before `ledger fix` refused (content, not clock), a stale built binary refused, the same F1 from two takes kept apart, phase and next command in `ledger status` | [10](docs/evidence/10-round-two.md) |
| The reader's hand-over by hook | watched in two whole loops under herdr: the reply saved verbatim, sent back once on a bad quote and repaired, tokens recorded, no user `CLAUDE.md` in the readers (it was in 11 of 26 before); 40 orchestrator tool calls and no Write, against 57 and 4 before; a `/compact` mid-loop survived | [10](docs/evidence/10-round-two.md) |
| Derail on one of the author's own skills | watched: contradictions in its text found that nobody planted; the fix did not change the behaviour it aimed at and the loop closed `open`, saying so | [10](docs/evidence/10-round-two.md) |
| Does the knowledge help? | measured on three build tasks, 3 runs per arm, graded by the probe: the CLI task ends with 4.0 findings without the plugin, 2.0 with the knowledge alone, 0 with the instruction to probe; the skill fires on plain wording; small MCP servers come out clean without the plugin | [10](docs/evidence/10-round-two.md) |
| TypeScript and Rust samples | compiled against the real packages (found a dead package name, a required field, a Zod 4 break); samples that need packages not installed here are checked for syntax only | [10](docs/evidence/10-round-two.md) |
| The plugin audits itself; three other stacks (Rust CLI, Python MCP server on the real SDK, bash + skill repo) | watched: found and fixed a data-loss bug in its own CLI; the derail loop ran on the bash + skill repo (receipts 4/4 on the last three takes) | [08](docs/evidence/08-self-audit.md) |
| `eval-emit` (scenario -> `claude plugin eval` case) | watched: one emitted case run by `claude plugin eval` with its no-plugin baseline (score 0.67 with the plugin, 0.33 without, on the seeded skill); 3 of 11 receipts expressible as graders, the rest are listed as not expressible | [08](docs/evidence/08-self-audit.md) |
| Authenticated MCP servers (OAuth) | not measured: reported as such, routed to `mcpc` / MCP Inspector | - |
| `design` skill | watched: picks the surface with labelled evidence and asks the interview of that surface; run for a CLI idea (no MCP question) and an MCP idea up to the second group; an approved sketch at the end was not run | [10](docs/evidence/10-round-two.md) |
| Windows | not tested (macOS/Linux/WSL intended) | - |

## What it replaces

The three skills `audit-agentic-cli`, `audit-agentic-mcp` and `audit-skill-by-derailment` (from `yigitkonur/skills-by-yigitkonur`). Their reference content is carried into `skills/agent-interface-design/references/` as small single-decision files; every heading of the sources is accounted for in [docs/parity/ledger.tsv](docs/parity/ledger.tsv), and [docs/parity/REPORT.md](docs/parity/REPORT.md) lists what changed shape and what was dropped, with reasons.

## Footprint

Always-on cost is about 309 tokens in total (`claude plugin details agentic-maker`): a short description for each of the five skills (about 40 for each of the three user-started commands, about 60 and 80 for the two knowledge skills) and about 50 for the reader. The skill bodies load only when a skill runs.

## Safety

- `probe mcp <command>` and `probe mcp .mcp.json` start that command (with the file's `env`) in an empty temp directory to ask it for `tools/list`: that is code from the repository being audited, so point it only at servers you would run anyway.
- Probes run only `--help`, `--version`, one invalid command, `--help` of subcommands named like read verbs (`list`, `show`, `get`, ...), anything you name with `--sub` or declare read-only with `--safe`; each in an empty temp directory with stdin closed, a timeout and its own process group. A script that does not read its arguments is not run at all. `agy` is never launched.
- A scenario is data that can come from a repository you did not write. Its `copy:` fixtures read only from inside the project and write only inside a fresh workspace; its `shell:` fixtures and `cmd` receipts are code and run as you. `run` checks the receipts when a take ends, so read them first: `run --dry-run` lists them (`receipts_run_after`), and `check receipts <take> --list` prints them without running anything.
- Fresh-agent runs use `--restricted` and an allowlist of tools and environment variables (what `claude` itself needs, plus a cloud provider's credentials only when `claude` is set to use that provider; the dry-run lists the names). The worker runs on a copy of a skill or plugin target, so a scenario that allows `Write` cannot change the real one. Destructive-capable targets need throwaway fixtures. Every run has a turn cap, a budget ceiling and a time limit, the cost preview comes before the spend, and the ledger's round limit and budget are enforced (`ledger fix` and `run --session` refuse past them; the budget counts the workers' dollars, the readers' tokens are shown in `ledger status`).
- Run records hold full transcripts, and every probe keeps its whole reply. The first write in a project creates `.agentic-maker/.gitignore` (`runs/`, `active/`) so they are not committed by accident; `scenarios/` stays committable.
- The plugin registers one hook besides the Stop gate: a `SubagentStop` hook scoped to `agentic-maker:trace-reader`, so it does nothing for any other subagent. It reads the hook payload, writes the reader's reply and checks it. The reader runs without your `CLAUDE.md` (`omitClaudeMd`). The in-session reader is read-only (`Read, Grep, Glob`).
- A live herdr round (optional; needs `herdr`) follows the rules of the `herdr-conductor` plugin when it is installed: one command per reply, never poll, never touch the session's own pane. Accepting the trust dialog for a scratch folder adds an entry to `~/.claude.json` (use `run --prepare --workspace-dir` to reuse one folder).
- No telemetry. The plugin's own code opens a network connection only for `probe mcp` against a URL you give it; fresh-agent runs start `claude`, which talks to the model API as it always does.

## Develop

`scripts/check.sh` (no network, no model): compiles on Python 3.9 and the current one, smoke-tests the CLI, lints the 300+ reference files (shape and size), checks links and generated indexes, injected-command safety, manifests (and that the three version numbers agree) and `claude plugin validate`, guards the scenario and probe safety rules, measures the always-on footprint, scans for personal data, and reports parity. See [AGENTS.md](AGENTS.md).

MIT licensed.
