# Synthesis: merging findings

> Read when: you have findings from several takes, scenarios, readers or repositories and must decide what to fix first.

<!-- src: audit-skill-by-derailment/references/forensic-subagent-briefs.md#3. Launching Multiple Auditor Subagents in Parallel -->
## Several readers at once

When several takes or sessions finished (five scenarios, a fleet of panes), spawn **one `trace-reader` per take**, at most five at a time (more than that is a workflow, not a loop). Confirm every take is complete first (receipts computed, status recorded). Each reader writes nothing; the orchestrator saves each reply as its own file so attribution is never ambiguous. As the reports come back, verify each with `check findings`, then cross-reference: a defect found by several readers or in several scenarios is **systemic**; one found once is scenario-specific. Fix systemic defects first, serially (one writer), and rerun.

## Merge rules

- Two findings are the same defect when they share the controlling text (same file and quote) or the same root code on the same step. Keep the clearest quote and list the other takes' refs.
- Rank: P0, then compound-P0 (three or more P1 in one phase), then P1 by number of takes that hit it, then P2.
- A `[NICE]` quote protects its line: no fix may remove it unless a finding supersedes it (`check nice`).
- If takes disagree (one triggered the skill, one did not), report the rate, not a verdict; that is the T1 signal.

<!-- src: audit-skill-by-derailment/references/herdr-pane-audit.md#5. Multi-Repository Cross-Pattern Matrix Template -->
## Cross-pattern matrix (fleet audits)

Before editing the target, summarize a multi-session audit in one table:

| Session / pane | Repository | Archetype | Delivered | Derailments / omissions | Root cause | Corrective action |
|---|---|---|---|---|---|---|
| `<id>` | `<repo>` | e.g. dual-engine, monorepo, static site, no-build | scripts, docs, local tests | e.g. tunnel tested with `--help` only | M4, C3 | add a `probe` action |
| `<id>` | `<repo>` | monorepo | scripts, docs | missed the CI build script | S3, C4 | add a monorepo CI recipe |
| `<id>` | `<repo>` | static site | full local build | skipped remote triggers | C1, M1 | add a two-tier contract |
| `<id>` | `<repo>` | no-build | contract checks | left a 30 KB workflow un-audited | C2, O1 | add staged deprecation |

The rows are the shape of the old template with the repository names removed; the codes show how one table feeds the fix list.
