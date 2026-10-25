# Changelog

## 0.4.0 - 2026-10-25

- feat(skills): build-cli and build-mcp, build-skill fixed by derail, derail leave_out, shipped scenario packs (#7) (7c822b3)
- ci: release.py v2 (shipped-file filter, nested manifests, both tag forms, Release-Level trailer, --plugin for multi-plugin marketplaces) (11ae046)

## 0.3.0 - 2026-10-25

- feat(skills): /agentic-maker:build-skill creates, redesigns or merges a skill: facts verified first, layout, frontmatter, body, ship checklist, then tested with fresh agents through derail; twelve reference pages re-cut from build-skill (frontmatter facts checked against Claude Code 2.1) (da21afa)
- ci(release): manual runs only on main, check out the newest main, no rebase after the gate (fail and let the queued run release), refuse a tag that exists, empty Unreleased section handled (Codex review) (607ab39)
- ci(release): every shipped change on main gets a version, tag and release by itself (scripts/release.py decides the bump from commit types; the workflow commits, tags and publishes), README documents the auto-update setting, AGENTS.md says not to bump by hand (99ce525)
- docs(readme): project-scope install that stays off until enabled (marketplace add, install, disable, enable with --scope project; tested in a fresh config) (04c8c3e)

## 0.2.1 - 2026-10-21

- README rewritten in a plainer, lowercase voice. Install now leads with the one-line shell command, `claude plugin install agentic-maker --marketplace yigitkonur/plugin-agentic-maker`, run in an empty config with and without a GitHub ssh key (Claude Code retries over https). `/plugin marketplace add` and `/plugin install` were run in a real session too: the plugin is active at once, and `/agentic-maker:audit` worked in that session.
- Three TypeScript samples fixed after their packages were installed and type-checked, which round two had left at syntax only: `AgentExecutor` and `createOpenAIToolsAgent` come from `@langchain/classic/agents` (`langchain` 1.5 has no `./agents`); an OpenAI tool call is narrowed to `type === 'function'` before `.function` is read (`openai` 7.39); `prom-client` is deprecated in favour of `@prometheus-io/client`. Every npm import in the samples now resolves; what is left are names a sample takes from another page, user files and the Workers runtime types.
- The clean twin (the audit's false-positive control) was audited again from an ordinary session and was not clean: extra positional arguments were dropped silently (`get 1 2 --json` returned item 1, exit 0; two Medium findings from the probe, rated High by the audit), and `delete` of an item that does not exist succeeded. It now refuses both (exit 2 `unexpected_argument`, exit 3 `item_not_found`), its help examples match the real output and show the error envelope, and it lists only exit codes it uses. The default probe and every probe set the audits chose report 0 findings.
- A live Codex worker was run (`codex exec` on the seeded CLI task) and read by id: `--from session:<id>` found the rollout, the trace keeps Codex's exit codes, receipts 3/3, the reader's finding verified after one hook send-back. `--from herdr:<pane>` resolved a live Codex pane through its status line.

Known gaps: the interactive Codex TUI on this machine could not refresh its login (`codex exec` could); a Codex worker reads its own memory folder, so it is not a clean room the way a `--restricted` Claude worker is. The OpenTelemetry sample still uses `@opentelemetry/sdk-trace-node` 2.x, deprecated in favour of `@opentelemetry/sdk-trace` 3.0, which has no drop-in `NodeTracerProvider`.

## 0.2.0 - 2026-10-21

Two review rounds on 0.1.0, from the top, each claim checked before it was edited and each change watched running (`docs/evidence/09-second-review.md`, `docs/evidence/10-round-two.md`). 0.1.1 was never tagged; its changes are in this release.

**The loop is witnessed by the machine, not by the orchestrator's say-so**
- `run` checks the scenario's Receipts when a take ends (the dry-run lists them first; a `cmd` receipt runs through /bin/sh). `ledger close --outcome clean` is refused (`not_witnessed`) until every fix has a passing rerun-predicate verdict from a take that ran after it and the newest take's receipts pass; the refusal names the command that fixes it. `ledger judge` records the orchestrator's own verdict, with a reason, when a predicate cannot decide.
- `ledger status` reports the phase (`framing`, `reading`, `fixing`, `rerunning`, `judging`, `closing`) and the next command; every error that carries a runnable suggestion also carries it as `next_actions`. Findings are keyed by findings file and id (two readers both number F1). `ledger fix` refuses a controlling file whose content changed since the last recorded run (`edited_before_fix`), and `run` refuses a built CLI older than its sources (`stale_bin`). A round is a batch of fixes followed by a rerun; `--rounds` and `--budget-usd` are enforced (`rounds_exhausted`, `budget_exhausted`, exit 5). `check diff --session` judges an edit against the copy kept at `ledger fix`, and flags a rule added beside an unchanged cause even when something else was deleted.
- `check findings` accepts a quote that begins with the `trace.md` label, derives `--trace` from where the findings file sits, and refuses an `order` predicate whose two calls are the same; regex predicates are matched per event, with line anchors. Text rules that patched these (write plain characters, quote after the label, do not anchor) are gone.

**The reader hands its findings over by hook**
- A `SubagentStop` hook (`hooks/hooks.json`, matcher `agentic-maker:trace-reader`) saves the reader's reply exactly as written, runs `check findings`, sends the reply back once with the reasons if a quote does not verify, and records the reader's tokens. The orchestrator copies nothing. `trace-reader` carries `omitClaudeMd: true`: before, the user's `CLAUDE.md` was in 11 of 26 reader transcripts. Seen in two whole loops under herdr: 40 orchestrator tool calls and no Write (the same kind of loop took 57 and 4 Writes), both readers repaired their own quotes, a `/compact` in the middle was survived.
- Reader cost is shown as tokens in `ledger status`; the budget counts the workers' dollars.

**Sessions that already exist**
- `normalize session:<id>` and `run --runner existing --from session:<id> | herdr:<pane>` find a Claude Code, Codex or agy session by id; a new agy adapter, Codex command exit codes and the Claude running cost are read. `skills/derail/references/session-recipes.md` has the same reading as plain `jq`; the Python adapters and the recipes agree event for event on a real session of each harness.
- `derail` recognises a skill only the user can start (`disable-model-invocation: true`): the scenario prompt starts it with a slash command and T1 is reported as not observable. Run on one of the author's own skills it found contradictions nobody had planted.

**Steering**
- `agent-interface-design` has a description in plain words, a "check what you built" section (run `agentic-maker probe cli|mcp` on your own work) and generated routing by stack. Built tasks with and without the plugin: the CLI task ends with 0 probe findings against 4.0 without the plugin and 2.0 with the knowledge but no probe instruction; the skill fires on "build an MCP server" and "add a tool" where it fired 0 of 3 before. `probe` keeps its whole reply (`evidence_file`).
- `design` asks the interview of the surface chosen (MCP, CLI or skill), not always the MCP one. Ten eval cases (five that must stay quiet).

**Safety, honesty, content**
- Workers run on a copy of a skill or plugin target; the worker environment is an allowlist that excludes the orchestrator's messaging and herdr variables; `.agentic-maker/.gitignore` keeps run records out of git.
- The TypeScript (98) and Rust (6) samples in `frameworks/` were compiled against the real packages; this found a dead npm package name (`@vercel/mcp-adapter` is a stub; `mcp-handler`), a required OAuth field, a Zod 4 break and fragments that were not valid syntax. MCP authorization, elicitation, sampling and `_meta` pages corrected against the 2025-11-25 specification; one tool-count ladder; one severity rubric. The "clean" CLI fixture was not clean under a full audit (6 gaps) and is now.
- Removed: the rule "one Bash call per message" (seven calls in a controlling test, no prompt).

**Known gaps**
- No live Codex worker run: Codex asked to log in again, a step only the user can do. Codex and agy ingestion is checked on recorded sessions. Authenticated (OAuth) MCP servers are not measured; Windows is untested; the `design` interview was run for one CLI and one MCP idea up to its second group, not through to an approved sketch.
- Reader cost is not in dollars. Third-party packages not installed here (`openai`, `ioredis`, `@langchain/*` and others) leave their samples checked for syntax only.
- Four pre-approved `agentic-maker` commands asked for approval once in a long manual-permission loop in round one; a controlled test could not reproduce it.
- A small design question ("add a tool to our MCP server that deletes events: write its definition") is answered without loading the skill (1 of 3); the same request as work on code fires it every time.
- Deferred to a later release: a `probe skill` (skills are checked by `derail` runs and by reading), freezing a scenario's receipts with a hash at `ledger init`, re-checking the seven `fresh/` pages dated before 2026-01, and merging the hybrid sections that `decisions/surface-choice.md` and `decisions/mcp-vs-cli-hybrids.md` both carry.

## 0.1.0 - 2026-10-20

First release. Built from the plan in `docs/design/` and checked against Claude Code 2.1.302 and herdr 0.9.5 (see `docs/what-is-true.md` and `docs/evidence/`).

- Commands: `/agentic-maker:audit`, `:derail`, `:design`; model-invoked `agent-interface-design` and `derailment-method`; the read-only `trace-reader` agent.
- CLI: `doctor`, `detect`, `scan`, `probe cli|cli-diff|mcp`, `run`, `normalize`, `check receipts|findings|diff|predicate|nice`, `ledger`, `eval-emit`.
- Reference content carried over from `audit-agentic-cli`, `audit-agentic-mcp` and `audit-skill-by-derailment`, re-cut to single-decision files, with the inherited defects reconciled (see `docs/migration-brief.md`).
- Checked before release: the plugin audited its own CLI with its own `audit` skill (two runs) and the findings were fixed or documented; the derail loop was run on a seeded skill and on a bash + skill repo; the probes were run on a Rust CLI and on a Python MCP server built on the real SDK; two live herdr rounds. See `docs/evidence/`.
- Known gaps: no live Codex or agy worker; authenticated MCP servers are not measured; the rest of the `design` interview needs a person and was not run; Windows is untested; scenario proposal by `derail` when none exist was not run headlessly; the model-level self-audit was not rerun after the last round of fixes.
