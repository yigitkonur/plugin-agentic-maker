# Calling a CLI from an Agent

> Read when: you are writing or reviewing the wrapper that a calling agent uses to run a CLI: invocation, exit-code routing, retry, error recovery, batches, and failure triage.

Code: Python in `../frameworks/python/agent-integration.md`, TypeScript in `../frameworks/node/agent-integration.md`, Go in `../frameworks/go/agent-integration.md`. Resilience patterns are in `caller-resilience.md`; prompt, tool schema and flag reference in `caller-agent-wiring.md`. The envelope is defined in `envelope-and-errors.md`.

<!-- src: audit-agentic-cli/references/agent-integration.md#1. Basic CLI Invocation Pattern -->
## Basic invocation

1. Append `--json` to the command and run it with a timeout (default 30 s).
2. Capture stdout and stderr separately.
3. If stdout is non-empty, parse it as the envelope (`ok`, `result`, `error`). This holds for failures too, because the envelope is always on stdout.
4. If stdout is empty: exit 0 means `{ok: true, result: null}`; any other exit means an error with code `exit_<n>` and the stderr text (or "Unknown error") as the message.
5. On timeout, return an error with code `timeout` and `retryable: true`.
6. If stdout is not valid JSON, return an error with code `invalid_json` and the parser message.

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#Exit Codes | audit-agentic-cli/references/discovery-and-auth.md#Exit Codes~2 | audit-agentic-cli/references/agent-integration.md#2. Exit Code Routing | audit-agentic-cli/references/examples.md#Standard Exit Codes -->
## Exit-code routing

Route on the exit code first, then read the body. The canonical table is in `exit-codes.md`; this is the caller's view.

| Code | Name | Caller action | Retryable | Example |
|------|------|---------------|-----------|---------|
| `0` | success | Proceed with the result | N/A | `mycli deploy` deployed |
| `1` | crash | Abort, log, report the bug, escalate to a human | Maybe | nil pointer, unhandled exception |
| `2` | usage | Fix the command syntax | No | `mycli --invalid-flag` |
| `3` | not_found | Handle the missing resource (create it first) | No | `mycli get user xyz` |
| `4` | auth | Re-authenticate | No | expired token, insufficient permissions |
| `5` | conflict | Resolve the state conflict, then retry | No | `mycli create foo` already exists |
| `6` | validation | Fix the input data | No | `mycli set --port 999999` |
| `7` | transient | Retry with backoff | Yes | network timeout, rate limit, 503 |
| `8` | partial | Read the per-item results and handle failures | No (check details) | batch where some items failed |

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#Scripting with Exit Codes -->
## Scripting with exit codes

```bash
#!/bin/bash
mycli deploy my-app --env prod
case $? in
    0) echo "Deploy succeeded" ;;
    4) echo "Auth failed - re-authenticate"; mycli auth login ;;
    7) echo "Transient error - retrying..."; sleep 5; mycli deploy my-app --env prod ;;
    *) echo "Fatal error"; exit 1 ;;
esac
```

<!-- src: audit-agentic-cli/references/agent-integration.md#3. Retry Logic with Exponential Backoff -->
## Retry with exponential backoff

- Defaults: `max_retries` 3 (so up to 4 attempts), `base_delay` 1.0 s.
- Return immediately on success.
- Retry only when `error.retryable` is true (exit 7 when there is no body). Fail fast otherwise.
- Return the last result when attempts run out.
- Delay before retry `n` (from 0): `base_delay * 2^n + uniform(0, 1)` seconds, the jitter.
- Honour the server hint: if the error carries `retry_after`, wait `max(delay, retry_after)`.

<!-- src: audit-agentic-cli/references/agent-integration.md#4. Error Recovery Flow -->
## Error recovery by class

Map `error.class` to the next step:

| Class | Recovery |
|-------|----------|
| `auth` | Re-run `mycli auth login` |
| `not_found` | The resource does not exist; create it first |
| `conflict` | Use `--force` or resolve it; show `error.suggestion` |
| `validation` | Show `error.message`, apply `error.suggestion` |
| `rate_limit` | Wait `error.retry_after` seconds (60 if absent), then retry |
| exit-7 group (`rate_limit`, `timeout`, `network`, `dependency_failed`) | Temporary failure; the retry loop handles it |
| anything else | Report `error.message` |

<!-- src: audit-agentic-cli/references/agent-integration.md#5. Batch Processing with Partial Failure -->
## Batch processing with partial failure

- Work through the items in batches (default 10), invoking the retry wrapper per item.
- Collect `succeeded` (item plus result), `failed` (item plus error) and `total`.
- Report the outcome as partial (exit 8) when both lists are non-empty.

> Note: read-only and idempotent batches default to continue and report partial (exit 8); destructive batches default to stop at the first error. `--stop-on-error` / `--continue-on-error` override either.

<!-- src: audit-agentic-cli/references/agent-integration.md#9. Debugging Agent CLI Failures -->
## Debugging agent CLI failures

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Agent loops infinitely | No exit code differentiation | Implement semantic exit codes |
| Parser errors | Mixed stdout/stderr | Separate streams properly |
| Timeouts | Interactive prompts | Add `--yes` / `--no-input` flags |
| Retry storms | No Retry-After header | Add header to rate limit responses |
| Partial data | Pagination not handled | Return `result.next_cursor` and `result.has_more`, implement `--all` |

> Note: the pagination fields are `result.items`, `result.next_cursor`, `result.has_more` and optional `result.total`.
