# Exit Codes

> Read when: you are assigning, documenting or auditing the exit codes of a CLI an agent drives.

<!-- src: audit-agentic-cli/references/output-contracts.md#3. Exit Code Taxonomy | audit-agentic-cli/references/output-contracts.md#Standard Exit Code Table -->
## The one canonical table

Exit codes let an agent make retry decisions without parsing output.

| Code | Name | When to Use | Retry? | Error Classes |
|------|------|-------------|--------|---------------|
| 0 | `success` | Operation completed successfully | N/A | none |
| 1 | `crash` | Unexpected error, internal failure, panic | Maybe | `internal` |
| 2 | `usage` | Bad flags, invalid arguments, wrong syntax | No | `usage` |
| 3 | `not_found` | Requested resource does not exist | No | `not_found` |
| 4 | `auth` | Authentication or authorization failed | No | `auth` |
| 5 | `conflict` | Resource already exists, version mismatch, lock contention | No (check details) | `conflict` |
| 6 | `validation` | Input validation failed (schema, format, constraints) | No | `validation` |
| 7 | `transient` | Retryable error (network, timeout, rate limit, dependency) | Yes | `rate_limit`, `timeout`, `network`, `dependency_failed` |
| 8 | `partial` | Some operations succeeded, some failed | No (check details) | `partial_success` |

> Critical: exit codes must be documented explicitly in `--help` output and man pages.

> Note: the table is 0-8 with 1 = crash (unexpected/internal), and partial is 8, never 3. `transient` is the name of the exit-7 group, not an error class.

<!-- src: audit-agentic-cli/references/output-contracts.md#Exit Code Decision Tree -->
## Decision tree

```
Did the operation succeed?
  FULLY      -> exit 0  success
  PARTIALLY  -> exit 8  partial
  NO         -> what went wrong?
      User's fault
          bad arguments? -> exit 2  usage
          bad input?     -> exit 6  validation
      Our fault          -> exit 1  crash
      External fault
          retryable?     -> exit 7  transient
          not retryable? -> exit 4 auth / exit 5 conflict
                            (missing resource -> exit 3 not_found)
```

The source diagram drew the not-retryable external branch as `4/5` only; `not_found` (3) is the third not-retryable outcome in the table above.

<!-- src: audit-agentic-cli/references/output-contracts.md#Exit Code Quick Reference -->
## Quick reference

| Code | Name | Retry? | Action |
|------|------|--------|--------|
| 0 | success | N/A | Operation succeeded |
| 1 | crash | Maybe | Internal error: check logs |
| 2 | usage | No | Fix command syntax |
| 3 | not_found | No | Resource doesn't exist |
| 4 | auth | No | Check credentials |
| 5 | conflict | No | Handle conflict (force/rename) |
| 6 | validation | No | Fix input format/values |
| 7 | transient | Yes | Retry with exponential backoff |
| 8 | partial | Check | Inspect succeeded/failed lists |

## Rules around the table

- Define named constants instead of magic numbers: see `../frameworks/go/output-contracts.md` (Go), and the Python, Node and Rust files beside it.
- A non-interactive confirmation that cannot proceed exits 2 (`non-interactive.md`).
- Exit code, error `class` and stdout envelope must agree (`envelope-and-errors.md`).
- Retry rules per code and class: `retry.md`. Batch exit 8: `batch-and-partial.md`.
- Signal-driven exits (130, 137, 143) and a timeout exit override: `timeouts-and-signals.md`.
