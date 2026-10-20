# Fix patterns

> Read when: you know the root cause and are writing the edit that removes it.

<!-- src: audit-skill-by-derailment/references/fix-patterns.md#Fix Patterns -->
Match the root cause to a pattern, then apply it to the source text that caused the miss. The default move is to rewrite the controlling paragraph and its paired example so the right path becomes the natural one. `agentic-maker check diff` looks at the applied edit and flags one thing: new "always / never / must" text sitting next to a controlling sentence that did not change.

<!-- src: audit-skill-by-derailment/references/fix-patterns.md#1. Prerequisite Surfacing (cures S1) -->
## 1. Prerequisite Surfacing (cures S1)
Add prerequisites **before** step 1, with a verification command and a fallback.

<!-- src: audit-skill-by-derailment/references/fix-patterns.md#2. Threshold Concretization (cures M1) -->
## 2. Threshold Concretization (cures M1)
Add two or three concrete examples for each side of the boundary, plus a testable rule of thumb.

<!-- src: audit-skill-by-derailment/references/fix-patterns.md#3. Workflow Path Reconciliation (cures S2) -->
## 3. Workflow Path Reconciliation (cures S2)
Name both paths, present them in the same section, and add selection criteria.

<!-- src: audit-skill-by-derailment/references/fix-patterns.md#4. Output Location Specification (cures M2) -->
## 4. Output Location Specification (cures M2)
Specify an exact relative path, anchored on a landmark the executor already knows.

<!-- src: audit-skill-by-derailment/references/fix-patterns.md#5. Execution Method Specification (cures M4) -->
## 5. Execution Method Specification (cures M4)
State the tool, what to observe and how to record it.

<!-- src: audit-skill-by-derailment/references/fix-patterns.md#6. Format Alignment (cures M3) -->
## 6. Format Alignment (cures M3)
One canonical format, documented once. A conversion note at every alternate boundary.

<!-- src: audit-skill-by-derailment/references/fix-patterns.md#7. Scaling Guidance (cures M5, O4) -->
## 7. Scaling Guidance (cures M5, O4)
Add an explicit rule that changes the instruction by input size.

<!-- src: audit-skill-by-derailment/references/fix-patterns.md#8. Conditional Gating -->
## 8. Conditional Gating
Put a gate at the top of the step: "Only execute if [condition]. Skip to step N for [other path]."

<!-- src: audit-skill-by-derailment/references/fix-patterns.md#9. Schema Duplication at Point of Use (cures S3) -->
## 9. Schema Duplication at Point of Use (cures S3)
If the schema has ten items or fewer, duplicate it where it is used. If larger, cross-reference it by exact section name.

<!-- src: audit-skill-by-derailment/references/fix-patterns.md#10. Harness Alignment (cures O6) -->
## 10. Harness Alignment (cures O6)
Remove test-harness-only constraints that are not part of the real contract. Judge the executor against the skill, not against wrapper instructions you added for the test. This includes the runner's own restrictions: if the sandbox hides files the skill tells the agent to read, fix the sandbox.

<!-- src: audit-skill-by-derailment/references/fix-patterns.md#11. Source Rewrite First -->
## 11. Source Rewrite First
If one sentence, example or routing table caused the miss, rewrite or delete that source. Do not keep bad text and add a warning beside it unless both are truly needed.

<!-- src: audit-skill-by-derailment/references/fix-patterns.md#12. Two-Tier Verification Enclosure (cures C1) -->
## 12. Two-Tier Verification Enclosure (cures C1)
Split verification into two mandatory tiers:
- **Tier 1, hermetic local proof:** autonomous, zero-risk, runs locally in every session.
- **Tier 2, remote infrastructure proof:** a live probe, automated trigger binding, operational checks.

The agent must reach Tier 1 before it may consider Tier 2, which removes the premature-completion illusion.

<!-- src: audit-skill-by-derailment/references/fix-patterns.md#13. Staged Deprecation & Safe Neutralization (cures C2) -->
## 13. Staged Deprecation and Safe Neutralization (cures C2)
When changing or deleting existing infrastructure (for example CI workflows), prescribe the four steps `Categorize` -> `Shadow` -> `Flip Required Check` -> `Neutralize Triggers`. It removes the agent's hesitation over destructive actions.

<!-- src: audit-skill-by-derailment/references/fix-patterns.md#14. Actionable Pre-Flight Probe Injection (cures C3) -->
## 14. Actionable Pre-Flight Probe Injection (cures C3)
Provide a fast, non-blocking `--dry-run` or `probe` command (under one second) for tools that start long-running daemons, so the agent does not fall back to `--help` and skip the real health check.

<!-- src: audit-skill-by-derailment/references/fix-patterns.md#15. Rigid Phase Gating & Canonical Layout Enforcement (cures C4, S3) -->
## 15. Rigid Phase Gating and Canonical Layout Enforcement (cures C4, S3)
Structure the workflow into numbered phases with strict, checkable exit conditions. Mandate exact relative directory layouts (for example `scripts/dev/` versus `scripts/ci/`) to stop path drift across multi-package repositories.

## Patterns for the codes added in this plugin

16. **Trigger Rewrite (cures T1).** Rewrite the `description` (and, if opaque, the name) in the words a user says. Lead with the job, then the situations and obvious synonyms. A jargon description that is correct but never matches an everyday request is the defect.
17. **Trigger Differentiation / Narrowing (cures T2, T3).** Say what this target does that its nearest neighbour does not; add the negative case ("not for ..."); delete overlapping phrases from both descriptions.
18. **Boundary Rewrite (cures M7).** Start each tool or subcommand description with a distinct Verb + Resource and state what it does not do. If two cannot be told apart, merge them.
19. **Response Rewrite (cures O7).** Put the verdict first (`ok`, `failed`, `partial`), label truncated and partial results, and keep success and failure shapes visibly different.
20. **Budget Cut (cures O8).** Shorten definitions, cap and paginate responses, add a concise mode, prune the tool list.
21. **Loop Breaker (cures C5).** The error message says what to change before retrying and caps the retries.

<!-- src: audit-skill-by-derailment/references/fix-patterns.md#Anti-pattern: Errata files -->
## Anti-pattern: errata files
Never create separate "errata", "known issues", output-summary or mistake-notebook documents. Fixes go directly into the source. Run directories under `.agentic-maker/runs/` are disposable evidence and are not committed.
