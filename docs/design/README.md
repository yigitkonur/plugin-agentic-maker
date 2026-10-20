# `agentic-maker` — plan for a native Claude Code plugin

**Status: this was the plan; the plugin is now built (v0.1.0).** This folder is a record of what was decided and why, not a specification. Where it and the shipped plugin disagree, the plugin, [what-is-true.md](../what-is-true.md) (what was checked against a real Claude Code) and [evidence/](../evidence/) are right: the plan's unknowns U1-U16 were answered by running things, and some answers changed the design. Written 2026-10-20 from real reads of the three source skills, `plugin-swiftui`, the installed `herdr-conductor` plugin, live `herdr 0.9.5` / `codex` / `agy` `--help`, and the Claude Code docs. Working name `agentic-maker` (open question Q1).

One plugin replaces `audit-agentic-cli`, `audit-agentic-mcp` and `audit-skill-by-derailment`. It does two things for any agent-facing surface (CLI, script, MCP server/tool, skill):

1. **Design / audit** it against a surface-neutral contract, using runtime probes instead of regex-over-source.
2. **Test it by derailment**: a fresh agent attempts a realistic task, the whole execution is read, drift is traced to the *text or affordance that caused it*, that text is rewritten (not patched with rules), and the scenario is rerun.

## Read in this order

| File | What it answers |
|---|---|
| [01-evidence-and-findings](01-evidence-and-findings.md) | What was read; the 8 findings that changed the design; what each source skill really is; what `plugin-swiftui` teaches |
| [02-primitives-and-steering](02-primitives-and-steering.md) | Which Claude Code primitives exist today and which are used; **where each piece of knowledge arrives and why**; hooks kept / conditional / rejected |
| [03-derailment-loop](03-derailment-loop.md) | The loop as a native feature: runners, trace sources, scenarios, clean room, reader, the fix discipline, stop criteria, target kinds |
| [04-design-and-audit](04-design-and-audit.md) | The surface-neutral contract; `/agentic-maker:audit` and `/agentic-maker:design`; staying language-agnostic; the three-project test |
| [05-layout](05-layout.md) | The directory tree and why each part exists |
| [06-parity-ledger](06-parity-ledger.md) | Where every important idea from the three skills lands (file level) |
| [07-build-and-retire](07-build-and-retire.md) | Milestones M0–M6, the gate for deleting the originals, the 16 unknowns (U1–U16) |
| [08-open-questions-and-readback](08-open-questions-and-readback.md) | 16 open questions with recommended defaults; the four read-back questions answered |
| [09-execution-meta-plan](09-execution-meta-plan.md) | **How we build it:** steps S0–S10 with proof per step, decisions A1–A10 (plugin renamed `agentic-maker`), the M0 experiment table, delegation, risk branches, publish gate |
| [appendix-b](appendix-b-inherited-defects.md) | 25 defects found in the sources — fixed at migration, never copied |
| [appendix-c](appendix-c-review-log.md) | What an adversarial review changed, each item verified against the docs first |

**Section map** (the text cross-references `§` numbers from the original single document): §0–3 → 01 · §4–5 → 02 · §6 → 03 · §7, §9 → 04 · §8 → 05 · §10 → 06 · §11–12 → 07 · §13–14 → 08 · Appendix A → end of 01 · Appendix B → appendix-b · Appendix C → appendix-c.

## The shape in one paragraph

Three user-invoked skills (`audit`, `design`, `derail`; zero context cost until typed), two knowledge skills that arrive at the moment they prevent a failure (`agent-interface-design` when someone writes an agent-facing tool; `derailment-method`, preloaded into the reader), **one read-only subagent** (`trace-reader`, tools `Read/Grep/Glob`), a **five-command `agentic-maker` CLI in `bin/`** (python3 stdlib; output follows the contract it preaches), **at most one hook** (a hardened `Stop` gate that refuses "fixed" without a fresh trace), and per-surface references that are loaded on demand. Always-on cost: three short descriptions. Adding a target kind or a scenario = a file, not a restructure.

## The decisions that matter most

1. **Trace sources are ranked by trust**, replacing "toggle Ctrl+O and grep the scrollback": harness-written structured record (stream-json / session JSONL / rollout) → terminal scrollback → the agent's own report (a claim, never evidence).
2. **Scenarios never name the target**, and a new root-cause family **T (trigger)** exists — the old Modes A/C handed the worker the skill's path, hiding the most common skill failure.
3. **The reader is read-only and its findings are verified before any edit** (verbatim quotes in the trace, valid fields); fixes are checked on the *applied* diff for "added a rule instead of fixing the cause"; reruns use machine-checkable predicates.
4. **Workers report through files, not callbacks**; herdr is driven by `herdr-conductor`'s rules (never poll, never touch the own pane), not re-documented.
5. **Hooks are strict**: one kept (H2), two only on evidence, ten rejected with reasons.
6. **Ship order is reversed from the brief**: derail a skill first (`existing` + `headless` need no launch machinery), then CLI, then live/multi-harness, then MCP — so the loop exists to test the migrated knowledge.

## Open questions needing your input

Full list with defaults in [08](08-open-questions-and-readback.md). The ones most likely to change the build: **Q2** default runner (headless inner rounds + one live herdr round), **Q4** isolation default (hinges on U1/U13), **Q8** the one canonical exit-code table (0–8; the sources disagree), **Q14** ship order, **Q15** hook count (one vs. zero in v1).

## Next step

**M0 — spike, no plugin** ([07](07-build-and-retire.md)): resolve U1–U16 with real runs on one skill and edit this plan with what is true before writing any code.
