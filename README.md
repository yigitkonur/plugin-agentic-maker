# agentic-maker

a claude code plugin for building tools that agents actually use well, and for catching the exact moment your agent goes off the rails when they don't.

tl;dr, it does two things:

- **design + audit** a cli, script, mcp server or skill against one eight-question contract. the probes run the thing the way an agent would. no regex-over-source vibes.
- **derail** it: spin up a fresh agent on a realistic task, read the whole execution, find where it drifted, rewrite the text that caused the drift (not a "do / don't" rule bolted on next to it), rerun.

works on any project, any language. the probes hit the public interface (an executable, an mcp endpoint, a skill's text), and the language-specific stuff lives in reference files that only get read when they're needed.

## install

one line, from your shell:

```sh
claude plugin install agentic-maker --marketplace yigitkonur/plugin-agentic-maker
```

that adds the marketplace (in your user settings) and installs the plugin in one go. no github ssh key? no stress: claude code retries over https on its own, and the repo is public.

rather do it from inside claude code? same result, two slash commands, and the plugin is live in that session right away:

```
/plugin marketplace add yigitkonur/plugin-agentic-maker
/plugin install agentic-maker@plugin-agentic-maker
```

after the shell install, start a new session so the plugin loads. check it landed, pull updates later, or bail:

```sh
claude plugin list                                            # agentic-maker@plugin-agentic-maker, 0.2.1, enabled
claude plugin marketplace update plugin-agentic-maker && claude plugin update agentic-maker@plugin-agentic-maker
claude plugin uninstall agentic-maker@plugin-agentic-maker
```

want it in one project only, installed but switched off until you need it? use project scope (this edits that project's `.claude/settings.json` and nothing global):

```sh
cd your-project
claude plugin marketplace add yigitkonur/plugin-agentic-maker --scope project
claude plugin install agentic-maker@plugin-agentic-maker --scope project
claude plugin disable agentic-maker@plugin-agentic-maker --scope project   # installed, off
claude plugin enable agentic-maker@plugin-agentic-maker --scope project    # on, whenever you want it
```

(`claude plugin list` shows it as `Scope: project` with `✘ disabled` or `✔ enabled`. commit `.claude/settings.json` if the team should get the same setup, or leave it out of git if it's just you.)

## updates

every merge to `main` that changes the plugin gets a new version, a git tag and a github release by itself (`.github/workflows/release.yml`; commit types decide patch, minor or major, docs-only changes don't release). claude code only updates a plugin when its version changes, which is why that's automatic.

third-party marketplaces don't auto-update unless you switch it on. two ways:

- in claude code: `/plugin` → Marketplaces → plugin-agentic-maker → Enable auto-update
- in settings (user or project `settings.json`), as a key on the marketplace entry:

```json
{
  "extraKnownMarketplaces": {
    "plugin-agentic-maker": {
      "source": { "source": "github", "repo": "yigitkonur/plugin-agentic-maker" },
      "autoUpdate": true
    }
  }
}
```

claude code checks after the first message of a session (random delay of up to ten minutes), updates the files on disk, and loads the new version next time you start it (or `/reload-plugins`). manual route any time: `claude plugin marketplace update plugin-agentic-maker && claude plugin update agentic-maker@plugin-agentic-maker`.

## requirements

what you need: `python3` 3.9+ (standard library only, zero deps to install) and, for fresh-agent runs, `claude` on PATH. built and tested on claude code 2.1.304; `claude plugin eval` (used by `eval-emit`) needs 2.1.269 or later. optional extras: `herdr` (live interactive rounds, and finding a pane's session), `git` (only for `check diff` without `--session`), `jq` (only if you want the recipes in `skills/derail/references/session-recipes.md`). that's the whole list.

still running the three skills this replaces (`audit-agentic-cli`, `audit-agentic-mcp`, `audit-skill-by-derailment`)? read [docs/parity/REPORT.md](docs/parity/REPORT.md), then disable them. they fight over the same requests.

## try it

point it at something you've got:

```
/agentic-maker:audit ./bin/mytool          # a CLI: runs --help, --version, one invalid command and the read-only commands you allow
/agentic-maker:derail skills/my-skill      # a skill: fresh agents on realistic tasks, then fixes the text that misled them
/agentic-maker:design a tool that lists and cancels our scheduled backups
```

an audit ends in a scorecard plus findings, each with its evidence. here's a slice of a real one, on the plugin's own "clean" fixture cli before it got fixed (yes, the control had bugs; yes, they're fixed now):

```
Overall: 75 (7 of 8 measured). Contract is the lowest measured dimension.
F1. High: unknown flags are silently accepted and the command succeeds
    Evidence: `list --bogus --json` exited 0 and returned the normal item list
    Fix: reject any unrecognised option with exit 2, class `usage`, naming the flag
    Verify: agentic-maker probe cli clean-cli --safe "list --bogus --json # expect-exit 2"
```

a derail run ends with what changed and what's still open, and it flat out refuses to say "clean" without proof. from a real run on one skill (3 takes, $0.12):

```
ledger: closed clean | receipts 8/11, 9/11, 11/11 | F1-F5 fixed, each with a passing verdict from a take that ran after the fix
$ agentic-maker ledger close --outcome clean      (before the rerun)
error [conflict/not_witnessed]: the loop cannot be closed as clean: 8 of 11 receipts fail in the newest take; ...#F1: no rerun-predicate verdict is recorded
  next: agentic-maker run release-notes --session ...
```

## commands

| command | what it does |
|---|---|
| `/agentic-maker:audit <target>` | probes a cli, script, mcp server or skill and reports against the contract: scorecard plus evidence. it's told to change nothing; it runs in a forked agent with the usual tools, so that's an instruction, not a sandbox. |
| `/agentic-maker:derail <target>` | the loop: scenarios, fresh agents in a clean room, a read-only reader whose reply a hook saves and checks, a fix of the controlling text, a rerun, and a ledger that refuses "clean" until each fix is witnessed (plus a stop gate that refuses "fixed" without a fresh run). |
| `/agentic-maker:design <idea>` | picks cli, mcp or skill, asks the interview for that surface, and sketches it before anyone writes code. |
| `/agentic-maker:build-skill <idea or path>` | creates, redesigns or merges a skill: facts verified first (uses the `research` plugin when installed), layout, frontmatter, body, a ship checklist, then the fresh-agent loop above to test it. |
| `agent-interface-design` (model-invoked) | write-time guidance while an agent-facing surface is being built or reviewed; tells the model to run `agentic-maker probe` on what it just built. |
| `derailment-method` (model-invoked, narrow) | the vocabulary and discipline of the method; preloaded into the reader. |

the cli behind all of it is `agentic-maker` (on PATH while the plugin is enabled): `doctor`, `detect`, `scan`, `probe cli|cli-diff|mcp` (each keeps its whole reply under `.agentic-maker/runs/audit-<date>/`), `run`, `normalize` (a file, `session:<id>` or `herdr:<pane>`), `check receipts|findings|diff|predicate|nice`, `ledger init|status|fix|judge|close|abandon`, `eval-emit`. one json envelope on stdout when piped, diagnostics on stderr, exit codes 0-8, never a prompt. `agentic-maker <command> --help` has examples and the exit-code table.

## how a derail run works

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

why it's built like this, with the evidence: [docs/what-is-true.md](docs/what-is-true.md) (the questions put to a real claude code, U1-U16 and the findings E1-E20; most answered by running something, a few only partly or not at all, and it says which), [docs/evidence/](docs/evidence/) (one file per capability, with the runs), [docs/design/](docs/design/README.md) (the plan this was built from).

## status (what's proven, what isn't)

no cap, every row says what was actually watched on 2026-10-20 and 21 (claude code 2.1.302 to 2.1.304, herdr 0.9.5, macos) and what wasn't. "fixture-tested" means exercised on planted-defect fixtures that live in this repo. model runs are single samples: the numbers are in `docs/evidence/`, the raw stream records aren't in the repo (they carry session metadata). `scripts/check.sh` guards the probes, the findings check, the containment rules, links, manifests and footprint; the receipts, the witnessed ledger, `check diff`, predicates, the reader hook, `[NICE]` and the stop gate were watched in the runs below, not regression-tested.

| capability | status | evidence |
|---|---|---|
| derail loop on a skill (headless, clean room) | watched working, the whole loop with no human in it | [04](docs/evidence/04-derail-loop.md) |
| stop gate blocks a premature "fixed" | watched working in the real harness | [04](docs/evidence/04-derail-loop.md) |
| `audit` of a cli (`probe cli`) | watched working; fixture-tested: 10 of 11 planted defects found directly, 11 counting causes (the old script: 4, or 5); the clean twin stays silent under the default probe and under the extra probes a full audit picked (the twin wasn't clean twice: 6 gaps found by a full audit, fixed in 0.2.0; extra arguments silently dropped, found by an audit in a real session, fixed in 0.2.1) | [05](docs/evidence/05-audit-cli.md), [09](docs/evidence/09-second-review.md) |
| `audit` of an mcp server (`probe mcp`, stdio and http) | watched working; the budget matches a hand count | [06](docs/evidence/06-audit-mcp.md) |
| round limit, budget ceiling and the per-fix snapshot of `check diff` | watched: `rounds_exhausted` and `budget_exhausted` (exit 5), a rule added beside an unchanged cause gets flagged, a rewritten cause passes | [09](docs/evidence/09-second-review.md) |
| derail loop on a cli and on an mcp server | watched working on the seeded fixtures, one scenario each: the reader found a harness-induced stop (O6) on the cli and tools listed with no handler on the mcp server; fixes verified by 3/3 receipts on two reruns | [09](docs/evidence/09-second-review.md) |
| `claude plugin eval` over `evals/` | watched: 10 cases, 3 runs each, with and without the plugin (mean Δ +0.40): the five stay-quiet cases score 1.00 / 1.00; the trigger cases written in plain words fire (+1.00), except a small "write this tool's definition" question, which gets answered without the skill (1 of 3) | [10](docs/evidence/10-round-two.md) |
| live herdr round with a claude worker | watched working, two rounds; receipts 11/11 (the first round needed an ingest fix first, the second passed straight away) | [07](docs/evidence/07-live-herdr.md) |
| ingest a claude session transcript or `stream-json` | watched working | 04, 07 |
| codex sessions | a live codex worker (`codex exec` on the seeded cli task) read by id: rollout found, exit codes kept, receipts 3/3, the reader's finding verified; a live codex pane resolved with `herdr:<pane>`; the adapter matches the `jq` recipes event for event (28 events). heads-up: a codex worker reads its own memory folder, so it's not a clean room like a `--restricted` claude worker | [10](docs/evidence/10-round-two.md) |
| agy | never launched by the plugin (a launch can have effects it can't see); a session you already ran is read from its transcript by id or herdr pane (matches the recipes on a real session, 20 events) | [10](docs/evidence/10-round-two.md) |
| the ledger as witness | watched: `clean` refused until each fix has a passing verdict from a take that ran after it, an edit before `ledger fix` refused (content, not clock), a stale built binary refused, the same F1 from two takes kept apart, phase and next command in `ledger status` | [10](docs/evidence/10-round-two.md) |
| the reader's hand-over by hook | watched in three whole loops under herdr: the reply saved verbatim, sent back once on a bad quote and repaired, tokens recorded, no user `CLAUDE.md` in any reader (it was in 11 of 26 before), no file written by hand by the orchestrator in the two loops counted (4 Writes before); a `/compact` mid-loop survived; the last loop, on the 0.2.0 text, closed `open` because one fix didn't change the behaviour, and said so | [10](docs/evidence/10-round-two.md) |
| derail on one of the author's own skills | watched: contradictions in its text that nobody planted; the fix didn't change the behaviour it aimed at and the loop closed `open`, saying so | [10](docs/evidence/10-round-two.md) |
| does the knowledge help? | measured on three build tasks, 3 runs per arm, graded by the probe: the cli task ends with 4.0 findings without the plugin, 2.0 with the knowledge alone, 0 with the instruction to probe; the skill fires on plain wording; small mcp servers come out clean without the plugin too | [10](docs/evidence/10-round-two.md) |
| typescript and rust samples | compiled against the real packages, third-party ones included (caught a dead package name, a required field, a zod 4 break, a moved langchain import, an openai union type, a deprecated `prom-client`); every npm import resolves; what's left are names a sample borrows from another page | [10](docs/evidence/10-round-two.md) |
| the plugin audits itself; three other stacks (rust cli, python mcp server on the real sdk, bash + skill repo) | watched: found and fixed a data-loss bug in its own cli; the derail loop ran on the bash + skill repo (receipts 4/4 on the last three takes) | [08](docs/evidence/08-self-audit.md) |
| `eval-emit` (scenario -> `claude plugin eval` case) | watched: one emitted case run by `claude plugin eval` with its no-plugin baseline (0.67 with the plugin, 0.33 without, on the seeded skill); 3 of 11 receipts expressible as graders, the rest listed as not expressible | [08](docs/evidence/08-self-audit.md) |
| install from github | watched: the one-liner above in an empty config (with and without an ssh key), `list`, `details`, `update`, `uninstall`; the two slash commands in a real session, then `/agentic-maker:audit` in that same session | [10](docs/evidence/10-round-two.md) |
| authenticated mcp servers (oauth) | not measured: reported as such, routed to `mcpc` / mcp inspector | - |
| `design` skill | watched: picks the surface with labelled evidence and asks that surface's interview; run for a cli idea (no mcp question) and an mcp idea up to the second group; an approved sketch at the end wasn't run | [10](docs/evidence/10-round-two.md) |
| windows | not tested (macos/linux/wsl intended) | - |

## what it replaces

the three skills `audit-agentic-cli`, `audit-agentic-mcp` and `audit-skill-by-derailment` (from `yigitkonur/skills-by-yigitkonur`). their reference content got carried into `skills/agent-interface-design/references/` as small single-decision files; every heading of the sources is accounted for in [docs/parity/ledger.tsv](docs/parity/ledger.tsv), and [docs/parity/REPORT.md](docs/parity/REPORT.md) lists what changed shape and what got dropped, with reasons.

## footprint

lowkey light: about 365 tokens always-on, total (`claude plugin details agentic-maker@plugin-agentic-maker`). that's a short description per skill (about 40 each for the four commands you start, 60 and 100 for the two knowledge skills) plus about 50 for the reader. the `SubagentStop` hook costs no model context. skill bodies load only when a skill actually runs.

## safety (the boring part that matters)

- `probe mcp <command>` and `probe mcp .mcp.json` start that command (with the file's `env`) in an empty temp directory to ask it for `tools/list`. that's code from the repo being audited, so only point it at servers you'd run anyway.
- probes only run `--help`, `--version`, one invalid command, `--help` of subcommands named like read verbs (`list`, `show`, `get`, ...), and anything you name with `--sub` or declare read-only with `--safe`; each in an empty temp directory with stdin closed, a timeout and its own process group. a script that doesn't read its arguments isn't run at all. `agy` is never launched.
- a scenario is data that can come from a repo you didn't write. its `copy:` fixtures read only from inside the project and write only inside a fresh workspace; its `shell:` fixtures and `cmd` receipts are code and run as you. `run` checks the receipts when a take ends, so read them first: `run --dry-run` lists them (`receipts_run_after`), and `check receipts <take> --list` prints them without running anything.
- fresh-agent runs use `--restricted` and an allowlist of tools and environment variables (what `claude` itself needs, plus a cloud provider's credentials only when `claude` is set to use that provider; the dry-run lists the names). the worker runs on a copy of a skill or plugin target, so a scenario that allows `Write` can't touch the real one. destructive-capable targets need throwaway fixtures. every run has a turn cap, a budget ceiling and a time limit, the cost preview comes before the spend, and the ledger's round limit and budget are enforced (`ledger fix` and `run --session` refuse past them; the budget counts the workers' dollars, the readers' tokens show up in `ledger status`).
- run records hold full transcripts, and every probe keeps its whole reply. the first write in a project creates `.agentic-maker/.gitignore` (`runs/`, `active/`) so none of it gets committed by accident; `scenarios/` stays committable.
- the plugin registers one hook besides the stop gate: a `SubagentStop` hook scoped to `agentic-maker:trace-reader`, so it does nothing for any other subagent. it reads the hook payload, writes the reader's reply and checks it. the reader runs without your `CLAUDE.md` (`omitClaudeMd`). the in-session reader is read-only (`Read, Grep, Glob`).
- a live herdr round (optional; needs `herdr`) follows the rules of the `herdr-conductor` plugin when it's installed: one command per reply, never poll, never touch the session's own pane. accepting the trust dialog for a scratch folder adds an entry to `~/.claude.json` (use `run --prepare --workspace-dir` to reuse one folder).
- no telemetry. the plugin's own code opens a network connection only for `probe mcp` against a url you give it; fresh-agent runs start `claude`, which talks to the model api like it always does.

## develop

`scripts/check.sh` (no network, no model): compiles on python 3.9 and the current one, smoke-tests the cli, lints the 300+ reference files (shape and size), checks links and generated indexes, injected-command safety, manifests (and that the three version numbers agree) and `claude plugin validate`, guards the scenario and probe safety rules, measures the always-on footprint, scans for personal data, and reports parity. see [AGENTS.md](AGENTS.md).

mit licensed.
