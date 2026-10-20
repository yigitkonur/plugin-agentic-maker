# Changelog

## 0.1.0 - 2026-10-20

First release. Built from the plan in `docs/design/` and checked against Claude Code 2.1.302 and herdr 0.9.5 (see `docs/what-is-true.md` and `docs/evidence/`).

- Commands: `/agentic-maker:audit`, `:derail`, `:design`; model-invoked `agent-interface-design` and `derailment-method`; the read-only `trace-reader` agent.
- CLI: `doctor`, `detect`, `scan`, `probe cli|cli-diff|mcp`, `run`, `normalize`, `check receipts|findings|diff|predicate|nice`, `ledger`, `eval-emit`.
- Reference content carried over from `audit-agentic-cli`, `audit-agentic-mcp` and `audit-skill-by-derailment`, re-cut to single-decision files, with the inherited defects reconciled (see `docs/migration-brief.md`).
- Known gaps: no live Codex or agy worker; authenticated MCP servers are not measured; the `design` interview was not run end to end; Windows untested.
