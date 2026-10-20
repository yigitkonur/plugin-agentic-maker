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

Before recommending changes:

1. Inspect top-level help and each relevant subcommand. Use the help probe (see Probe commands below) to capture standard flags, examples and missing affordances.
2. Look for machine-readable output flags: `--json`, `--output json`, `--quiet`, `--fields`, `--jq`.
3. Test stdout/stderr separation on safe read-only commands.
4. Classify exit codes across success, usage, auth, not-found, validation, conflict and transient paths (`skills/agent-interface-design/references/cli/exit-codes.md`).
5. Probe non-interactive behaviour on prompt-prone commands.
6. Inspect destructive flow safety: `--dry-run`, `--yes`, `--force`, explicit confirmation semantics.
7. Verify help documents realistic examples, output fields and exit codes.
8. If auditing a CLI you have snapshotted before, diff the snapshots to spot command and flag drift.

Judge every result against `skills/agent-interface-design/references/cli/checks.md` (five core checks, severity, finish criteria). Fix the CLI before blaming the architecture.

<!-- src: audit-agentic-cli/SKILL.md#Bundled Scripts -->
## Probe commands

The two former shell scripts are replaced by plugin probes:

| Probe | Use for |
|---|---|
| `bin/agentic-maker probe cli` | Inspect top-level and subcommand help for standard flags, examples, exit-code docs and missing affordances; also runs checks on declared commands. |
| `bin/agentic-maker probe cli-diff` | Compare captured help snapshots for command/flag additions, removals and likely breaking changes. |

Read-only discovery support. Do not treat a probe as an agent-readiness proof: it covers discoverability and drift. It does not replace the stdout/stderr, exit-code, non-interactive and destructive-flow checks (steps 3 to 6); run those by hand with safe commands.

## Report shape

Audit report contents, in order:

1. Scorecard by audit dimension (the rubric is in `skills/audit/references/scoring.md`).
2. Severity-ranked findings.
3. Command evidence for each finding: the exact safe command plus observed stdout, stderr and exit code.
4. Why it matters for agents.
5. Recommended fix.
6. Verification command.

The other deliverable shapes (refactored CLI contract, iterative repair-loop design) are in `skills/design/references/cli-deliverables.md`.
