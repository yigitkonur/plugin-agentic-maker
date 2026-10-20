# Execution Patterns Overview

> Read when: you need the map of execution behaviours a CLI should cover, their priority, and the shared flag names.

<!-- src: audit-agentic-cli/references/execution-patterns.md#Execution Patterns for Agent-Friendly CLIs -->
## Scope

These patterns make CLI tools predictable, retry-safe and automation-friendly. This directory owns execution behaviour: retry, idempotency, dry-run, non-interactive, async, batch, timeout, pagination, rate-limit and continuation patterns.

<!-- src: audit-agentic-cli/references/execution-patterns.md#Summary: Agent-Friendly Execution Patterns -->
## Pattern priority

| Pattern | Key Benefit | Implementation Priority | File |
|---------|-------------|------------------------|------|
| **Idempotency** | Safe retries | High | `idempotency.md` |
| **Retry with backoff** | Handles transient failures | High | `retry.md` |
| **Dry-run** | Preview before commit | High | `dry-run.md` |
| **Non-interactive** | CI/CD compatibility | High | `non-interactive.md` |
| **Timeout handling** | Graceful deadline enforcement | High | `timeouts-and-signals.md` |
| **Pagination** | Efficient large dataset traversal | High | `pagination.md` |
| **Batch with partial failure** | Efficient bulk operations | Medium | `batch-and-partial.md` |
| **Batch limits** | Resource-safe bulk processing | Medium | `batch-limits.md` |
| **Rate limiting (client)** | Prevents throttling, respects quotas | Medium | `rate-limits.md` |
| **Long-running tasks** | Async operation support | Medium | `async-and-long-running.md` |
| **Transaction/rollback** | Atomic multi-step ops | Medium | `rollback.md` |
| **Timeout/cancellation** | Graceful failure handling | Medium | `timeouts-and-signals.md` |
| **Steering contract** | Better next-step selection | Medium | `../decisions/steering-contract.md` |
| **Bounded continuation** | Fewer turns in research/SEO loops | Medium | `continuation-modes.md` |

<!-- src: audit-agentic-cli/references/execution-patterns.md#Standard Flag Reference -->
## Standard flag reference

| Category | Flags |
|----------|-------|
| **Timeout** | `--timeout`, `--connect-timeout`, `--read-timeout`, `--graceful-shutdown-timeout`, `--on-timeout` |
| **Pagination** | `--per-page`, `--page`, `--cursor`, `--all`, `--max-pages`, `--sort-by`, `--sort-order` |
| **Batch** | `--batch-size`, `--max-concurrent`, `--delay-between-batches`, `--continue-on-error`, `--fail-threshold` |
| **Rate Limit** | `--rate-limit`, `--max-retries`, `--backoff-initial`, `--backoff-max`, `--respect-retry-after`, `--circuit-breaker-threshold` |
| **Continuation** | `--continuation-mode`, `--plan-next`, `--max-waves`, `--budget-queries`, `--emit-guidance` |
| **General** | `--dry-run`, `--yes`, `--force`, `--idempotency-key`, `--output`, `--quiet` |

All patterns should:

1. Return structured JSON output
2. Use clear exit codes
3. Provide sufficient context for automated recovery
4. Never hang waiting for human input
5. Use consistent `--kebab-case` flag naming
