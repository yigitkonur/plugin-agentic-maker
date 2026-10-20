# Changelog

## 0.1.1 - 2026-10-20

A second review of the 0.1.0 content, from the top, with each claim checked before it was edited (`docs/evidence/09-second-review.md`).

- Loop: `--rounds` and `--budget-usd` are enforced (`rounds_exhausted`, `budget_exhausted`, exit 5; reader cost is not metered). `check diff --session` judges an edit against a copy of the file kept at `ledger fix`, not against git `HEAD`, and flags a rule added beside an unchanged cause even when something else was deleted. Plugin targets are copied into the take. Workers no longer receive the orchestrator's messaging socket and token, session variables or cloud credentials unless that provider is in use; `run --dry-run` lists the names. `.agentic-maker/.gitignore` is written on the first state write. `run --dry-run` warns when a receipt expects a file the worker cannot write. `ledger close` resolves findings still marked `fixing`. Ctrl-C exits 130. Malformed receipts and numeric scenario names teach instead of crashing.
- Skills: `audit` steps are probe flags and the report closes by saying the target is not to be run by hand; `derail` passes `--rounds` to the ledger, lets the orchestrator read the worker's temp workspace, and warns that reader replies can arrive HTML-escaped; `trace-reader` carries a one-line meaning of every root-cause code and quotes after the `trace.md` label; `design` says which questions use AskUserQuestion.
- References: one tool-count ladder and one description-length rule; MCP authorization, elicitation, sampling, completion and `_meta` pages corrected against the 2025-11-25 specification; CLI contradictions closed (continuation modes, missing-flag class, `schema_version`, event names, steering block, one severity rubric for `cli/checks.md` and the audit); about 210 code-sample findings in `frameworks/` fixed, rejected or marked illustrative; 19 `fresh/` pages dated; an unfounded savings figure and a third party's address removed; 106 migration notes moved to `docs/parity/reconciled-notes.md`.
- Checks: `lint-refs.py` rejects `as_of: unknown`; `check-links.py` also verifies backticked `dir/file.md` paths; `check.sh` scans for email addresses.
- Watched: the derail loop on the skill (rounds, snapshot, budget, 11/11 receipts after the fix), on a CLI and on an MCP server; the audit of the seeded and the clean CLI; `claude plugin eval` over `evals/`. Not compiled: the TypeScript and Rust samples in `frameworks/` (no `tsc` or `rustfmt` here).
- Known gaps: four `agentic-maker` commands that `derail` pre-approves asked for approval once each in a manual-permission session, three of them when issued next to another tool call (`derail` now asks for one Bash call per message; effect not measured; one "yes" lets them through); an audit that adds its own probe commands finds ordinary gaps in the "clean" CLI fixture, which is clean only against the planted defects.

## 0.1.0 - 2026-10-20

First release. Built from the plan in `docs/design/` and checked against Claude Code 2.1.302 and herdr 0.9.5 (see `docs/what-is-true.md` and `docs/evidence/`).

- Commands: `/agentic-maker:audit`, `:derail`, `:design`; model-invoked `agent-interface-design` and `derailment-method`; the read-only `trace-reader` agent.
- CLI: `doctor`, `detect`, `scan`, `probe cli|cli-diff|mcp`, `run`, `normalize`, `check receipts|findings|diff|predicate|nice`, `ledger`, `eval-emit`.
- Reference content carried over from `audit-agentic-cli`, `audit-agentic-mcp` and `audit-skill-by-derailment`, re-cut to single-decision files, with the inherited defects reconciled (see `docs/migration-brief.md`).
- Checked before release: the plugin audited its own CLI with its own `audit` skill (two runs) and the findings were fixed or documented; the derail loop was run on a seeded skill and on a bash + skill repo; the probes were run on a Rust CLI and on a Python MCP server built on the real SDK; two live herdr rounds. See `docs/evidence/`.
- Known gaps: no live Codex or agy worker; authenticated MCP servers are not measured; the rest of the `design` interview needs a person and was not run; Windows is untested; scenario proposal by `derail` when none exist was not run headlessly; the model-level self-audit was not rerun after the last round of fixes.
