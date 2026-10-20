# Changelog

## 0.1.0 - 2026-10-20

First release. Built from the plan in `docs/design/` and checked against Claude Code 2.1.302 and herdr 0.9.5 (see `docs/what-is-true.md` and `docs/evidence/`).

- Commands: `/agentic-maker:audit`, `:derail`, `:design`; model-invoked `agent-interface-design` and `derailment-method`; the read-only `trace-reader` agent.
- CLI: `doctor`, `detect`, `scan`, `probe cli|cli-diff|mcp`, `run`, `normalize`, `check receipts|findings|diff|predicate|nice`, `ledger`, `eval-emit`.
- Reference content carried over from `audit-agentic-cli`, `audit-agentic-mcp` and `audit-skill-by-derailment`, re-cut to single-decision files, with the inherited defects reconciled (see `docs/migration-brief.md`).
- Checked before release: the plugin audited its own CLI with its own `audit` skill (two runs) and the findings were fixed or documented; the derail loop was run on a seeded skill and on a bash + skill repo; the probes were run on a Rust CLI and on a Python MCP server built on the real SDK; two live herdr rounds. See `docs/evidence/`.
- Known gaps: no live Codex or agy worker; authenticated MCP servers are not measured; the rest of the `design` interview needs a person and was not run; Windows is untested; scenario proposal by `derail` when none exist was not run headlessly; the model-level self-audit was not rerun after the last round of fixes.
