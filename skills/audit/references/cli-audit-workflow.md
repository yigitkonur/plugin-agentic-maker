# CLI Audit Workflow

> Read when: the task is to audit a CLI for agent or LLM use (JSON output, exit codes, non-interactive behaviour) and you need the trigger, the steps and the report shape.

<!-- src: audit-agentic-cli/SKILL.md#When To Use -->
## When this workflow applies

Use it for CLI-only agent-readiness work, for example:

- "make my CLI agent-friendly" or "audit CLI for LLM use"
- the agent keeps failing to parse a CLI result
- stdout mixes JSON with progress text or spinners
- every failure exits 1 with no structured error body
- a command hangs waiting for an interactive prompt
- the workflow validates, rejects, repairs and resubmits a generated artifact
- a fresh CLI needs agent-first constraints from day one
- help text is unreliable as a contract for an agent caller

Do not use it for:

- **Surface choice (CLI vs MCP vs hybrid).** Make the surface decision first (`skills/agent-interface-design/references/decisions/surface-choice.md`). Only after the surface is fixed as CLI does this workflow apply.
- **MCP server audits, schemas, transports, auth or context budgets.** Use the MCP audit and the MCP references (`skills/agent-interface-design/references/mcp/hard-rules.md`); an optional implementation or live-verification companion may exist, if installed.
- **Vendor CLI operations** when a vendor-specific skill exists; use that skill.
- **Generic shell scripting** unrelated to the CLI's agent contract.

<!-- src: audit-agentic-cli/SKILL.md#Audit Workflow -->
## Steps

Before recommending changes, run the checks through the probe, in this order (the target is never run by hand; `agentic-maker probe cli --help` lists the flags):

1. **Help and discoverability.** `agentic-maker probe cli <binary>` captures top-level help and `--version`, runs one invalid command, and reports standard flags, examples and exit-code documentation. Add `--sub "<subcommand>"` for each subcommand that matters.
2. **Machine-readable output.** Read the probe's flag coverage (`--json`, `--output`, `--quiet`, `--fields`, `--jq`).
3. **stdout/stderr separation.** Declare read-only commands with `--safe "<args> --json"`; the probe parses stdout as JSON and reports JSON on stderr.
4. **Exit codes.** Add known failure cases as `--safe "<args> # expect-exit N"` and judge them against `skills/agent-interface-design/references/cli/exit-codes.md`.
5. **Non-interactive behaviour.** Every probe run has stdin closed and a timeout; a command that waits is a Critical finding.
6. **Destructive-flow safety.** Destructive-looking commands are never run: judge them from the help (`--dry-run`, `--yes`, `--force`, confirmation semantics) through the `destructive.*` findings. Name one with `--sub` to read its own `--help`.
7. **Examples, output fields and exit codes in help.** The probe's `help.*` findings.
8. **Drift.** For a CLI you snapshotted before, `agentic-maker probe cli-diff old.txt new.txt`.

Judge every result against `skills/agent-interface-design/references/cli/checks.md` (five core checks, severity, finish criteria). Fix the CLI before blaming the architecture.

<!-- src: audit-agentic-cli/SKILL.md#Bundled Scripts -->
## Probe commands

The two former shell scripts are replaced by plugin probes:

| Probe | Use for |
|---|---|
| `bin/agentic-maker probe cli` | Inspect top-level and subcommand help for standard flags, examples, exit-code docs and missing affordances; also runs checks on declared commands. |
| `bin/agentic-maker probe cli-diff` | Compare captured help snapshots for command/flag additions, removals and likely breaking changes. |

A probe is a black box over read-only commands, not an agent-readiness proof: it sees only the commands you declared with `--safe` and `--sub`. Whatever it did not run (destructive commands, anything behind auth) goes under "Not run" in the report; do not run it yourself to fill the gap.

## Report shape

Audit report contents, in order:

1. Scorecard by audit dimension (the rubric is in `skills/audit/references/scoring.md`).
2. Severity-ranked findings.
3. Command evidence for each finding: the exact safe command plus observed stdout, stderr and exit code.
4. Why it matters for agents.
5. Recommended fix.
6. Verification command.

The other deliverable shapes (refactored CLI contract, iterative repair-loop design) are in `skills/design/references/cli-deliverables.md`.
