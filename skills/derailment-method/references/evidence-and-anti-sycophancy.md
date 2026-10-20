# Evidence and anti-sycophancy

> Read when: you must decide whether "the task succeeded" is true, or you are writing the Receipts section of a scenario.

<!-- src: audit-skill-by-derailment/references/disk-evidence-and-anti-sycophancy.md#Disk Evidence & Anti-Sycophancy Verification Protocol -->
How to check what an agent really did, independently of what it says it did. In the plugin the checks are **receipts**: lines in a scenario's `## Receipts` section that `agentic-maker check receipts <take>` evaluates on the worker's workspace and records in `receipts.json` before the reader starts.

<!-- src: audit-skill-by-derailment/references/disk-evidence-and-anti-sycophancy.md#1. The "Self-Report Mirage" (Why LLM Receipts Lie) -->
## 1. The self-report mirage

Language models lean toward agreement and a tidy ending. In a long multi-step run an agent will often close with something like "Successfully produced and verified all outputs" while the system shows otherwise:
- a download timed out after 35 seconds and left a 0-byte `.tmp` file;
- the "result" is a 2 KB HTML error page from a CDN;
- a verification call threw an uncaught `TypeError` and never ran;
- the agent skipped step 4 because a selector was missing and moved on to step 5.

> **Claims in agent prose are unverified leads. Bits on disk and raw exit codes are the truth.**

Consequences: never accept a final report alone; never let the reader (also a model) treat the worker's summary as an observation; a run whose receipts fail is not a pass, whatever the agent said.

<!-- src: audit-skill-by-derailment/references/disk-evidence-and-anti-sycophancy.md#2. The 5 Pillars of Forensic Disk Evidence -->
## 2. The five gates and the receipt that implements each

Every claim of completion is checked against five gates.

<!-- src: audit-skill-by-derailment/references/disk-evidence-and-anti-sycophancy.md#Gate 1: Non-Zero Disk Presence -->
### Gate 1 - the artifact exists and is not empty
A path mentioned in prose proves nothing. Check existence and size. Receipts: `exists: out/report.md`, `nonempty: out/report.md`.

<!-- src: audit-skill-by-derailment/references/disk-evidence-and-anti-sycophancy.md#Gate 2: Magic Byte & MIME Type Header Validation -->
### Gate 2 - the content is the kind of thing its name says
A failed fetch often writes an error page or an empty container under the expected name; an extension does not guarantee valid data. Check the real type: `type: out/result.json json`, or a command receipt such as `cmd: file --brief out/archive.zip | grep -q "Zip archive" => 0`. Pick the check from the artifact kind; the plugin hard-codes no file type.

<!-- src: audit-skill-by-derailment/references/disk-evidence-and-anti-sycophancy.md#Gate 3: Structural JSON Schema & Delimiter Parsing -->
### Gate 3 - machine-readable output parses and has the required fields
When the task is supposed to leave a structured result, parse it and test the keys: `json: out/result.json status == "ok"`, `json: out/result.json items.0.id exists`. If a skill asks the agent to print a delimited receipt in its transcript, check the delimiters with a `regex:` receipt on the saved record.

<!-- src: audit-skill-by-derailment/references/disk-evidence-and-anti-sycophancy.md#Gate 4: Process Exit Code Verification -->
### Gate 4 - the commands really succeeded
The structured trace carries each tool result with its error flag and, for shell commands, the exit code (`exit` in `trace.norm.jsonl`). The reader searches those; for state the commands should have produced, use `cmd: ... => 0` receipts. In a terminal scrollback (a weaker source) search for the harness's failure phrases instead, and mark the finding's source accordingly.

<!-- src: audit-skill-by-derailment/references/disk-evidence-and-anti-sycophancy.md#Gate 5: Timeline & Timestamp Plausibility -->
### Gate 5 - the timeline is plausible
Compare file times with the run window. A file older than the run was recycled, not made. Receipt: `mtime-in-window: out/report.md`. Also use `unchanged: input.csv` for files that must not change and `no-extra-files: . allow=out/**` for files that appeared where nothing should.

<!-- src: audit-skill-by-derailment/references/disk-evidence-and-anti-sycophancy.md#3. Automated Artifact Auditing Recipe -->
## 3. The automated recipe

The old recipe was a shell loop over `find` printing name, byte size, `file` type and a VALID/SUSPICIOUS verdict for a hard-coded set of media extensions. It is replaced by `check receipts`, which prints one line per receipt with its detail (`2 bytes`, `mtime outside the run window (stale file?)`, `unexpected: scratch/tmp.dat`), covers any artifact kind through the receipt kinds above, and refuses paths that leave the workspace.

If a scenario has no `## Receipts`, `check receipts` says so, and completion rests on the agent's own report: write receipts for anything the task is meant to leave behind.
