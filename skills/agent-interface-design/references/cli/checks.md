# CLI Agent-Readiness Checks

> Read when: you are auditing, designing or repairing a CLI that an agent must drive, and need the pass/fail gate, severity and finish criteria.

<!-- src: audit-agentic-cli/SKILL.md#audit-agentic-cli -->
## The contract

Make a CLI an agent can drive without human babysitting. The contract: pure machine-readable stdout, semantic exit codes, non-interactive defaults, structured errors with retry guidance, and, for workflows that produce repairable artifacts, an iterative feedback loop the agent can finish on its own.

Rule: fix the CLI before blaming the architecture. When an agent fails to use a CLI, first check these five items and repair them; do not move the capability to a different surface (MCP server, wrapper, hybrid) until the CLI passes them. The surface decision itself is made first, in `../decisions/surface-choice.md`; this file applies once the surface is fixed as CLI.

<!-- src: audit-agentic-cli/SKILL.md#Five Core Audit Checks -->
## Five core checks

Before recommending features, verify these. If any fail, fix them first.

1. `--json` (or equivalent) exists and **stdout is pure machine output**: no progress, no banners, no prose.
2. Logs, spinners, banners, and progress go to **stderr**.
3. **Exit codes** distinguish success, usage error, auth, not-found, conflict, validation, and transient/retryable failures, not all `0` or `1` (`exit-codes.md`).
4. Headless runs **never block** without an explicit `--no-input`/`--yes` path or a clear non-interactive error (`non-interactive.md`).
5. Error responses include a stable **error code** and a **retryable** boolean (or equivalent guidance) (`envelope-and-errors.md`).

When a command must emit a non-JSON artifact (patch, diff, query, prompt, translation), keep stdout one canonical artifact format and put status on stderr or in a sidecar. Never mix prose into the data channel.

<!-- src: audit-agentic-cli/SKILL.md#Severity Rubric -->
## Severity in agent terms

Classify findings in agent terms, not human-UX terms.

| Severity | Use when |
|---|---|
| Critical | Agents cannot safely parse, continue, or avoid unintended side effects (e.g. JSON mixed with progress on stdout; destructive command with no `--dry-run`/`--yes`). |
| High | Agents act but are likely to fail, retry incorrectly, or block (e.g. prompt with no `--no-input`; opaque exit `1` for every error class). |
| Medium | Agents finish only with extra probing or brittle assumptions (e.g. undocumented output fields, missing help examples). |
| Low | Polish or consistency only (e.g. nonstandard alias when long flag is documented). |

How findings are scored is defined in the audit skill, not here.

<!-- src: audit-agentic-cli/SKILL.md#Local Exemplars -->
## What a strong CLI looks like

Two kinds of exemplar are worth looking for in the field, whichever CLIs you have installed:

- A strong agent-ready CLI: JSON everywhere, `--dry-run`, `--id-only`, non-pager flags, an exit-code contract, bulk-mutation gates.
- A drift-aware CLI: an installed-help snapshot, the upstream-versus-local distinction, refresh scripts, version-drift routing.

Names of specific companion skills are left out on purpose; see `../decisions/companion-routing.md` if installed.

<!-- src: audit-agentic-cli/SKILL.md#Finish Criteria -->
## Finish criteria

Do not call a CLI agent-ready until:

- The five core audit checks pass.
- The JSON envelope is stable enough to script against across commands.
- `--help` documents the command contract (examples, output fields, exit codes).
- A non-interactive run can succeed or fail deterministically with no human keystroke.
- Any iterative workflow returns enough structured feedback for an agent to repair without human interpretation (`repair-build-order.md`).

The full output checklist is `output-contract-checklist.md`.
