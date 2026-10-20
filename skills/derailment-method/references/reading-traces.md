# Reading a trace

> Read when: you are the reader (or the orchestrator reading one trace yourself) and need to know what drift looks like in the record.

<!-- src: audit-skill-by-derailment/references/forensic-subagent-briefs.md#Forensic Subagent Briefs & Mission-Style Prompt Templates -->
A trace is `trace.md`: one line per event, numbered `[n]`. The full text of event *n* is line *n* of `trace.norm.jsonl`. You cite events by number and quote them exactly; a script rejects any quote that is not verbatim in the events you cite.

<!-- src: audit-skill-by-derailment/references/forensic-subagent-briefs.md#2. Universal Forensic Auditor Subagent Brief Template -->
## Search by dimension

Walk the trace once per dimension. "Nothing found in this dimension" is a complete answer; do not pad.

| Dimension | Ask |
|---|---|
| **trigger** | Was the target chosen? If not, what did the agent say or do instead (T1)? Did a neighbour win (T2)? Did it fire when it should not (T3)? |
| **discovery** | Did it read the files the text points to? Which references were never opened (S4)? Did it go looking for something the text should have given (S3)? |
| **syntax and flags** | Any rejected flag, wrong argument, stale option (O5, M3, M4)? |
| **thresholds** | Where did it pick a number or a size on its own (M1)? |
| **paths and output** | Where did it write, and did the text say where (M2)? Files in unexpected places (S3, M2)? |
| **resilience** | Selectors, timeouts, edge-case input that broke a parser (O3, O4)? |
| **mental model** | Premature completion (C1), hesitation over a destructive step (C2), `--help` instead of running (C3), skipped checks (C4), repeated retries (C5)? |
| **recovery** | After an error, did the message tell it what to do? Did it invent a workaround (O1, O5)? |
| **completion** | Does the closing claim match the receipts? |
| **budget** | Did a definition or a response crowd out the task (O8)? |

<!-- src: audit-skill-by-derailment/references/herdr-pane-audit.md#3. Cognitive Mental Model Reconstruction Heuristics -->
## Reconstructing the mental model

Agents rarely announce `[STUCK]` or `[GUESSED]`. You infer the state from what they did. Thinking text is usually not exposed, so every belief you write is `inferred` unless a cited event contains the reasoning itself.

Signals, generalized from live-session audits:
- the same section re-read twice; a long pause before an ambiguous step (M1, M5);
- `--help` run where a real run was needed (C3);
- an error followed by a hand-built workaround (O1, O5);
- a step in the text that never appears in the trace (C4);
- "done" while the receipts fail (C1);
- files created in places the text never mentioned (M2, S3);
- a question to the user that the text should have answered (S1, M5);
- two instructions in conflict - note which one won (S2);
- a retry with an unchanged hypothesis (C5).

<!-- src: audit-skill-by-derailment/references/herdr-pane-audit.md#A. Detecting "Premature Completion Illusion" (C1) -->
### A. Premature completion illusion (C1)
- **Symptom:** the agent edits local files, runs one test or a linter, then prints "Migration complete" with no remote or end-to-end check.
- **Belief:** creating the files was the task.
- **Text defect:** the workflow has no phase gate with a checkable stop condition. Fix: Two-Tier Verification Enclosure, Rigid Phase Gating.

<!-- src: audit-skill-by-derailment/references/herdr-pane-audit.md#B. Detecting "Destructive / Mutation Hesitation" (C2) -->
### B. Destructive or mutation hesitation (C2)
- **Symptom:** the agent finds existing workflow files or service configs, inspects them and leaves them untouched.
- **Belief:** changing them might break production or a required check.
- **Text defect:** no non-destructive staged recipe (Shadow -> Flip Check -> Neutralize). Fix: Staged Deprecation.

<!-- src: audit-skill-by-derailment/references/herdr-pane-audit.md#C. Detecting "Tooling & Environment Ignorance" (C3) -->
### C. Tooling and environment ignorance (C3)
- **Symptom:** the agent runs `start --help` instead of `start` or `probe`, or skips a dashboard step because it does not know a browser-automation tool is available.
- **Belief:** a real run would lock the session with a daemon, or it does not know how to authenticate.
- **Text defect:** no fast non-blocking `--dry-run` / `probe`, and no explicit headless fallback. Fix: Actionable Pre-Flight Probe.

<!-- src: audit-skill-by-derailment/references/herdr-pane-audit.md#D. Detecting "Monorepo & Structural Drift" (S3 / C4) -->
### D. Monorepo and structural drift (S3 / C4)
- **Symptom:** in a monorepo the agent creates scripts in unexpected directories, or skips the CI build script because the root `package.json` has no single build command.
- **Belief:** workspace boundaries are unclear.
- **Text defect:** no monorepo workspace recipe. Fix: Canonical Layout Enforcement.

## Reading rules

1. Read `receipts.json` first; it tells you what the world looks like regardless of what the agent said.
2. Read the trace in order, in chunks. Do not skim to the end and work backwards from the closing claim.
3. A finding needs at least one cited event whose text contains your quote.
4. Look for what the text got right too. A `[NICE]` finding protects a sentence from the next rewrite.
5. If the run ended by `max_turns`, a budget or a timeout, the last events show where it was stuck; say that, and do not call it completed.
