# Friction taxonomy: markers, severity, root causes

> Read when: you are about to label a drift point with a marker, a severity and a root-cause code.

<!-- src: audit-skill-by-derailment/references/friction-taxonomy-guide.md#Comprehensive Friction Taxonomy & Root-Cause Analysis Guide -->
Every drift point gets one marker, one severity and one root-cause code. The first 21 codes (S1-S5, M1-M6, O1-O6, C1-C4) are frozen and keep their meaning. Codes marked *added* cover failures the original method could not see: whether the target is chosen at all (T), and what happens when the target is a CLI or an MCP tool (M7, O7, O8, C5).

<!-- src: audit-skill-by-derailment/references/friction-taxonomy-guide.md#1. The 4 Friction Markers -->
## The four markers

Tag every deviation or unexpected event in a trace with one of four markers.

| Marker | Severity | Definition | Example |
|---|---|---|---|
| `[STUCK]` | **P0** hard stop | The executor cannot proceed without outside help or unstated knowledge. | A modal blocks the page; a required token is missing; the output folder does not exist and the script does not create it. |
| `[BROKE]` | **P0 / P1** crash | A documented command, flag, API call or selector threw an unhandled error. | `page.isVisible()` does not exist; `--ratio 16:9` where the flag is `--aspect-ratio`; a script syntax error. |
| `[GUESSED]` | **P1** ambiguity gap | The executor invented a decision or parameter the text should have made explicit. | Choosing between two logged-in profiles; choosing 720p or 1080p unprompted. |
| `[NICE]` | **Keep** load-bearing | A specific instruction, pattern or check prevented an error. | A backdrop-escape rule stopped an intercepted click; an atomic `.tmp` check caught a corrupt download. **Never delete a line a `[NICE]` depends on.** |

In the plugin the **reader assigns markers from the trace**. Asking the worker to tag its own moments changes what it does and biases what it reports; self-annotation exists only as an optional cheap mode (`run --self-annotate`) with that bias stated.

<!-- src: audit-skill-by-derailment/references/friction-taxonomy-guide.md#2. Severity Hierarchy & Prioritization Rules -->
## Severity and priority

- **P0 (critical, blocker):** a hard stop or a crash that halted the workflow. Fix before anything else.
- **P1 (high, wasteful):** confusion, retry loops, path drift or guessed parameters that cost time but allowed continuation.
- **P2 (low, minor):** a wording ambiguity or cosmetic warning with no measurable delay.
- **Compound P0:** three or more P1 findings inside a single workflow phase count as one P0 for prioritization.

<!-- src: audit-skill-by-derailment/references/friction-taxonomy-guide.md#3. The 4 Root-Cause Families -->
## The root-cause families

Every drift point traces to a defect in the text or the tool. There are five families; **T** is added.

<!-- src: audit-skill-by-derailment/references/friction-taxonomy-guide.md#A. Structural Causes (`S`) -->
### S - structural (how information is organized, layered, connected)

- `S1` **Missing prerequisite:** a tool, binary, variable or parent folder is used before it is declared.
- `S2` **Contradictory paths:** two sections or files prescribe conflicting workflows or commands.
- `S3` **Scattered information:** a crucial instruction is split across files with no direct link.
- `S4` **Orphaned reference:** a file in `references/` is never linked from `SKILL.md`.
- `S5` **Circular dependency:** document A sends the reader to B and B sends the reader back to A.

<!-- src: audit-skill-by-derailment/references/friction-taxonomy-guide.md#B. Semantic Causes (`M`) -->
### M - semantic (phrasing, terminology, thresholds, specificity)

- `M1` **Ambiguous threshold:** a vague adjective ("substantial", "fast") with no number.
- `M2` **Unstated location:** the output path or naming convention is not given, so the agent guesses `/tmp` or the cwd.
- `M3` **Format inconsistency:** the same thing is written in two syntaxes.
- `M4` **Missing execution method:** the text says what to achieve but not the command or script that does it.
- `M5` **Assumed knowledge:** domain expertise or a hidden convention is not explained.
- `M6` **Vague verb:** "process", "handle" or "integrate" can be read several ways.
- `M7` **Ambiguous tool boundary** *(added)*: two tools, subcommands or skills have overlapping descriptions, so the agent picks the wrong one or alternates between them.

<!-- src: audit-skill-by-derailment/references/friction-taxonomy-guide.md#C. Operational Causes (`O`) -->
### O - operational (runtime mechanics, scripts, tools, environments)

- `O1` **Silent failure:** a command fails with no non-zero exit code or clear message.
- `O2` **Tool output mismatch:** a script emits a format or schema different from what `SKILL.md` documents.
- `O3` **Edge case unhandled:** valid input (a prompt with `%` or quotes) breaks the parser or selector.
- `O4` **Scaling breakdown:** it works on one file and hangs or crashes at realistic scale.
- `O5` **Stale reference:** a flag, version or selector that no longer exists is documented.
- `O6` **Harness-induced drift:** the test prompt or wrapper added constraints that are not in real use. (The runner itself can cause this: a sandbox that hides the skill's own reference files is O6.)
- `O7` **Response misread** *(added)*: the output was correct but its shape or wording led to a wrong conclusion - a table read as success, a warning read as an error, truncated output read as complete.
- `O8` **Budget blowup** *(added)*: a definition or response so large it crowded out the task (a 50 KB response, dozens of tool definitions).

<!-- src: audit-skill-by-derailment/references/friction-taxonomy-guide.md#D. Cognitive & Behavioral Causes (`C`) -->
### C - cognitive and behavioral (pacing and gating that make a model derail)

- `C1` **Premature completion illusion:** the agent treats producing local files as finishing, skipping remote or end-to-end gates.
- `C2` **Destructive or mutation hesitation:** the agent will not delete, overwrite or deprecate without explicit authorization.
- `C3` **Missing tooling awareness:** the agent runs `--help` or invents workarounds because it does not know a specialized tool exists.
- `C4` **Gate slack / step skipping:** steps have no checkable exit gate, so the model skims past verification.
- `C5` **Retry blindness / loop** *(added)*: the agent repeats the same failing action with an unchanged hypothesis.

### T - trigger *(added)*

The layer the original method could not see, because it handed the worker the skill's path. Here the worker gets an everyday request and the target is only available, as it would be for a user.

- `T1` **Not triggered:** the target fit the request and was available, but the agent never chose it (or only after being told). Evidence: no `Skill` or tool call for it, often a sentence like "I didn't need the skill".
- `T2` **Mis-triggered / collision:** a different skill or tool with an overlapping description won.
- `T3` **Over-triggered:** the target fired for a request outside its job.
