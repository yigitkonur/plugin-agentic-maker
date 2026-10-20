# Designing an Iterative Repair-Loop CLI

> Read when: you are designing the command set, the artifact channel and the validation of a CLI that agents use in a submit-and-repair loop.

The response contract, failure classes, anti-patterns and checklist are in `iterative-repair.md`.

<!-- src: audit-agentic-cli/references/iterative-cli.md#5. Case Study: Segmented Translation CLI | audit-agentic-cli/references/iterative-cli.md#Why this works especially well for SRT -->
## Case study: segmented translation

A CLI translates localization assets in batches. The workflow is a staged loop, not one `translate` command:

1. `init` creates a session and reports batch counts, language pair and the next command.
2. `batch` returns the next segment in a compact machine format, plus parseable guidance on where to save the result and how to submit it.
3. The agent translates only the requested entries.
4. `submit` validates the artifact and returns structured feedback on failure.
5. `status` reports progress and the next pending batch.
6. `finalize` rebuilds the final output when all required batches are complete.

The point is not localization; it is that the CLI keeps the agent inside a bounded repair loop. Line-oriented files made of numbered entries suit this because the input chunks naturally, context matters (so a batch can carry surrounding entries as read-only context), formatting mistakes are easy to validate, and partial completion is acceptable when session state is tracked. The CLI can therefore give the agent only the current slice, keep surrounding context without regenerating the whole file, validate missing entries, malformed structure or placeholder drift, say exactly which entries need repair, and continue batch by batch until finalization. Replace the entries with SQL migrations, JSON patches or generated config fragments and the loop is still valid.

<!-- src: audit-agentic-cli/references/iterative-cli.md#6. Designing The Artifact Channel -->
## Designing the artifact channel

Some workflows do not want JSON as the primary payload: a translation block, a unified diff, a SQL migration, a config fragment, a patch to review and resubmit. Then:

- keep the artifact in its native machine format;
- keep guidance parseable, not conversational;
- reserve a stable marker, trailer or companion command for metadata;
- make sure the agent can split artifact from guidance deterministically.

Acceptable: artifact on stdout with guidance under a reserved marker such as `#STATUS:` or `#GUIDANCE:`; artifact on stdout with machine-readable status from a separate `status` command; artifact written to a file with a structured JSON result.

Avoid: prose paragraphs between machine-readable lines; marker names or field types that change across commands; forcing the agent to scrape help text to recover from normal validation failures.

<!-- src: audit-agentic-cli/references/iterative-cli.md#7. Validation Design Rules -->
## Validation design rules

- Validate structure before semantics, and semantics before expensive downstream work.
- Return all repairable errors for the current artifact, not just the first.
- Separate hard failures from warnings.
- Preserve progress already completed.
- Make the retry budget explicit.
- Include both a machine code and a human fix suggestion when possible.

Useful dimensions: syntax or framing errors, missing or extra identifiers, count mismatches, placeholder preservation, cross-field consistency, batch or segment mismatches.

<!-- src: audit-agentic-cli/references/iterative-cli.md#8. Command Set Pattern -->
## Command set pattern

| Command | Purpose |
|---|---|
| `init` | Create session state and report next action |
| `fetch` or `batch` | Return the next unit of work |
| `submit` | Validate and accept or reject the artifact |
| `status` | Report progress and the next pending unit |
| `finalize` | Assemble final output |

The family separates planning state, artifact production, validation, progress inspection and completion. Collapsing them into one command makes the CLI harder for agents to recover from.
