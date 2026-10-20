---
name: derailment-method
description: How to find out why an agent drifted, guessed or stalled while using a skill, CLI, script or MCP tool - read the whole execution, name the text that misled it, rewrite that text instead of adding rules. Use when diagnosing "why did my agent skip / guess / ignore this". Not for code review.
user-invocable: false
---

<!-- src: audit-skill-by-derailment/SKILL.md#Audit Skill by Derailment: The Native Two-Tier Auditor -->
# Derailment method

A skill, a tool description, a `--help` page and an error message are a program that an LLM executes. When the agent drifts, the defect is in the text or affordance it was given. This method finds that text from the evidence of a real run and rewrites it. Two tiers do the work: a **worker** (a fresh agent that attempts a realistic task) and a **reader** (a read-only agent that studies the worker's whole execution). The orchestrator applies fixes and reruns.

<!-- src: audit-skill-by-derailment/SKILL.md#The 5 Non-Negotiable Invariants -->
## The five invariants

1. **Fix the text, not the executor.** Every remedy is an edit to the controlling text (a skill sentence, an example, a routing row, a tool description, an error message, a script) or to the tool itself. Never conclude "use a smarter agent". Rewrite or delete the sentence that misled; do not leave it and add a "do / don't" rule beside it.
2. **Claims are leads; the machine is the witness.** An agent's closing report is a claim. Verify exit codes and what is on disk (`agentic-maker check receipts`) before believing "done". See [evidence-and-anti-sycophancy](references/evidence-and-anti-sycophancy.md).
3. **Never judge from a view that hides what the agent did.** Read the harness's structured record (every tool call with full arguments, every result, hook events). A folded terminal view, a summary or the agent's own account is not evidence. Source ranking: `derail/references/trace-sources.md`.
4. **Search by dimension; do not chase a quota.** Cover trigger, discovery, syntax, thresholds, paths, recovery, completion and budget. "Nothing found in this dimension" is a valid answer; a list padded to a target length invites invented findings.
5. **No errata files.** The corrected source is the deliverable. A line marked `[NICE]` is load-bearing: never weaken or delete it without a finding that supersedes it.

## Every finding names two things

- the **controlling text**: the exact sentence, example, row, help line or message that led the agent there - or its **absence** (`ABSENT`) when nothing said what was needed;
- what the agent **believed** because of it, and whether that belief was `observed` (the trace shows reasoning) or `inferred` (reconstructed from what it did). Thinking text is usually not exposed, so most beliefs are inferred; say so.

Schema and handback rules: [finding-schema](references/finding-schema.md).

<!-- src: audit-skill-by-derailment/SKILL.md#Severity & Root-Cause Cheat Sheet -->
## Markers, severity, root cause (cheat sheet)

| Marker | Severity | Typical root cause | Fix family |
|---|---|---|---|
| `[STUCK]` cannot continue | P0 | S1 missing prerequisite, S2 contradiction, M2 unstated location | Prerequisite Surfacing, Path Reconciliation, Output Location |
| `[BROKE]` command or selector threw | P0 / P1 | O1 silent crash, O5 stale flag, O3 unhandled edge case | Error Recovery Addition, Option Modernization |
| `[GUESSED]` invented an unstated decision | P1 | M1 ambiguous threshold, M5 assumed knowledge | Threshold Concretization, Scaling Guidance |
| Premature completion, skipped gates | P1 | C1 completion illusion, C4 gate slack | Two-Tier Verification Enclosure, Rigid Phase Gating |
| Skipped destructive cleanup or mutation | P1 | C2 mutation hesitation | Staged Deprecation and Safe Neutralization |
| Ran `--help` instead of a real probe | P1 | C3 missing tooling awareness, M4 missing method | Actionable Pre-Flight Probe |
| Path drift or file recreation | P1 | S3 scattered information, M3 format inconsistency | Canonical Layout Enforcement |
| Target never chosen, or chosen wrongly | P1 | T1 not triggered, T2 collision, T3 over-triggered | Description rewrite at the trigger layer |
| `[NICE]` the text prevented an error | Keep | a load-bearing sentence or check | **Never weaken or delete** |

Three or more P1 findings in one phase collapse into a **compound P0**. The full code list (S1-S5, M1-M7, O1-O8, C1-C5, T1-T3) is in [taxonomy](references/taxonomy.md); the matching fix for each code is in [root-cause-matrix](references/root-cause-matrix.md) and [fix-patterns](references/fix-patterns.md).

## Read when

| File | Read when |
|---|---|
| [taxonomy](references/taxonomy.md) | assigning a marker, severity and root-cause code |
| [root-cause-matrix](references/root-cause-matrix.md) | choosing the fix for a code |
| [fix-patterns](references/fix-patterns.md) | writing the rewrite itself |
| [reading-traces](references/reading-traces.md) | reading a trace: what drift looks like and where to look |
| [evidence-and-anti-sycophancy](references/evidence-and-anti-sycophancy.md) | deciding whether "done" is true |
| [finding-schema](references/finding-schema.md) | producing or checking findings |
