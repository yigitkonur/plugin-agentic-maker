# Caller-Side Resilience

> Read when: you are adding auth refresh, conflict handling, a circuit breaker or a fallback around a CLI that an agent calls repeatedly.

TypeScript implementations are in `../frameworks/node/agent-integration-resilience.md`. Basic retry is in `caller-integration.md`; what to measure is in `caller-observability.md`.

<!-- src: audit-agentic-cli/references/agent-integration.md#12. Error Recovery Patterns -->
## Recovery patterns

Key each recovery on the exit code (`exit_4`, `exit_5`, `exit_7` in the wrapper's error code), recover once, and escalate rather than loop. An integration test script that checks the four basics (JSON output, not-found exit 3, error structure, non-interactive) is in `../frameworks/bash/agent-integration.md`.

<!-- src: audit-agentic-cli/references/agent-integration.md#Auth Token Refresh -->
## Auth token refresh

On exit 4:

1. Refresh the token through the token manager and retry the command once.
2. If the refresh throws, clear the stored token, run `auth login --yes`, and retry the command.

The token manager has three operations: `getToken`, `refreshToken`, `clearToken`. Interactive login is a human bootstrap (see `auth-and-secrets.md`); when no human is available, stop and report exit 4 instead of looping.

<!-- src: audit-agentic-cli/references/agent-integration.md#Conflict Resolution -->
## Conflict resolution

On exit 5, apply one of four strategies (default `merge`):

| Strategy | Action |
|----------|--------|
| `force` | Retry the command with `--force` |
| `merge` | Run `mycli resource merge --base <base_version> --current <current_version> --json --yes`; if it succeeds, retry the original command, otherwise return the merge result |
| `abort` | Return the conflict as-is |
| `prompt` | In an agent context, escalate to a human: error code `human_required`, message "Conflict requires human resolution: <message>", `retryable: false` |

<!-- src: audit-agentic-cli/references/agent-integration.md#Circuit Breaker Pattern -->
## Circuit breaker

Stop calling a CLI that keeps failing.

| State | Behaviour |
|-------|-----------|
| `CLOSED` | Normal operation |
| `OPEN` | Failing fast: raise "Circuit breaker is OPEN - failing fast" without running the command |
| `HALF_OPEN` | Testing recovery: one call is let through |

Rules:

- Defaults: `threshold` 5 consecutive failures, `resetTimeoutMs` 60000.
- A success resets the failure count to 0 and closes the circuit.
- A failure increments the count and records the time; at `threshold` the circuit opens.
- After `resetTimeout` has elapsed since the last failure, an open circuit moves to `HALF_OPEN` on the next call.
- The CLI example uses `threshold` 3 and `resetTimeoutMs` 30000. A non-retryable CLI error counts as a failure (it is thrown into the breaker); a retryable one is returned to the retry loop.

<!-- src: audit-agentic-cli/references/agent-integration.md#Graceful Degradation -->
## Graceful degradation

Wrap a primary call with a fallback and a predicate `shouldFallback(result)`. Example: if `mycli resource get id --json` fails with `exit_7` (transient), fall back to `mycli cache get id --json` and warn "Primary failed, attempting fallback...".