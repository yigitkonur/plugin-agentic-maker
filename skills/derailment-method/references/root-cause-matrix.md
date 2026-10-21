# Root cause to fix pattern matrix

> Read when: you have a root-cause code and need the fix pattern that cures it.

<!-- src: audit-skill-by-derailment/references/friction-taxonomy-guide.md#4. Comprehensive Root Cause to Fix Pattern Matrix (All 21 Codes) -->
Match the code, then apply the pattern **to the text that caused the miss** ([fix-patterns](fix-patterns.md) has the detail). The default move is to rewrite or delete the controlling text, not to add a warning beside it. Codes marked *added* extend the original 21.

| Code | Defect | Fix pattern |
|---|---|---|
| `S1` | Missing tool or prerequisite | **Prerequisite Surfacing:** add a pre-flight check with the exact install or config command before step 1. |
| `S2` | Contradictory workflows | **Path Reconciliation:** put the alternatives in one table with explicit if/then selection criteria. |
| `S3` | Scattered documentation | **Schema Duplication / Inlining:** place critical parameters and canonical schemas at the point of use. |
| `S4` | Orphaned reference | **Router Integration:** route every file in `references/` from `SKILL.md` with a "read when" trigger. |
| `S5` | Circular dependency | **Hierarchical Directionality:** a strict parent-router to leaf-reference topology with no back-links. |
| `M1` | Vague threshold | **Threshold Concretization:** replace adjectives with numeric boundaries (`> 100_000 bytes`, `<= 120 chars`). |
| `M2` | Unknown output location | **Output Location Specification:** give an exact path anchored on a directory the user knows. |
| `M3` | Format inconsistency | **Format Alignment:** one canonical syntax, documented once; conversion notes at boundaries. |
| `M4` | Missing command recipe | **Execution Method Specification:** exact copy-pasteable commands with every required flag. |
| `M5` | Assumed knowledge | **Scaling Guidance and Context Injection:** surface the implicit convention or scale rule in the text. |
| `M6` | Vague verb | **Actionable Verb Specification / Source Rewrite:** replace "process", "handle" with concrete operations. |
| `M7` | Ambiguous tool boundary *(added)* | **Boundary Rewrite:** each description starts with a distinct Verb + Resource and says what it does *not* do; merge tools that cannot be told apart. |
| `O1` | Silent crash | **Error Recovery Addition:** explicit error handling, non-zero exit codes and fallback instructions. |
| `O2` | Tool output mismatch | **Format Alignment:** reconcile the script's output schema with what `SKILL.md` expects. |
| `O3` | Edge case unhandled | **Edge Case Hardening:** input sanitization, delimiter escaping, explicit guards. |
| `O4` | Scaling breakdown | **Scaling Guidance:** batching, streaming pagination or concurrency limits for realistic scale. |
| `O5` | Stale CLI option | **Option Modernization:** update scripts and docs to the current runtime flags. |
| `O6` | Harness-induced drift | **Harness Alignment:** remove test-only constraints; judge the executor against the real contract. |
| `O7` | Response misread *(added)* | **Response Rewrite:** put the verdict first in the output, label partial and truncated results, keep success and failure shapes visibly different. |
| `O8` | Budget blowup *(added)* | **Budget Cut:** shorten definitions, cap and paginate responses, add a concise mode, prune the tool list. |
| `C1` | Premature completion | **Two-Tier Verification Enclosure:** phase-exit gates that need disk and exit-code proof. |
| `C2` | Mutation hesitation | **Staged Deprecation and Safe Neutralization:** the 4-step `Categorize` -> `Shadow` -> `Flip Required Check` -> `Neutralize Triggers` sequence. |
| `C3` | `--help` instead of running | **Actionable Fast Probes:** a sub-second `--probe` or `--dry-run` that proves readiness. |
| `C4` | Skipped verification | **Rigid Checkable Gates:** a machine-checkable marker or receipt that must exist before the next phase. |
| `C5` | Retry blindness *(added)* | **Loop Breaker:** the error names what changed or what to try instead and caps retries; state the cause in the message. |
| `T1` | Not triggered *(added)* | **Trigger Rewrite:** write the description in the words a user says, lead with the job and the situations, name the obvious synonyms. |
| `T2` | Collision *(added)* | **Trigger Differentiation:** state what this target does that its neighbour does not; remove the overlapping phrases. |
| `T3` | Over-triggered *(added)* | **Trigger Narrowing:** add the negative case ("not for ...") and tighten the verbs. |

> Note: the `C4` fix is a generic checkable marker or receipt; no delimiter string is built in.
