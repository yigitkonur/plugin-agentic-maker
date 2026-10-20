# Timeouts, Signals and Cancellation

> Read when: a command can run long enough to need deadlines, Ctrl+C handling or a defined cancellation result.

<!-- src: audit-agentic-cli/references/execution-patterns.md#8. Timeout and Cancellation | audit-agentic-cli/references/execution-patterns.md#CLI Timeout Flags -->
## Timeout flags

```bash
mycli long-operation \
  --timeout 5m \
  --connect-timeout 10s \
  --read-timeout 30s \
  --graceful-shutdown-timeout 30s        # Time allowed for cleanup

# Timeout with behavior control
mycli deploy \
  --timeout 10m \
  --timeout-exit-code 124 \
  --on-timeout cleanup                   # Action: cleanup | abort | preserve
```

> Reconciled: a timeout is class `timeout`, exit 7 (retryable). `--timeout-exit-code 124` is an explicit opt-in override; without it the exit is 7.

<!-- src: audit-agentic-cli/references/execution-patterns.md#Timeout Flag Standards -->
## Timeout flag standards

| Flag | Description | Default |
|------|-------------|---------|
| `--timeout <duration>` | Overall operation timeout | None (wait forever) |
| `--connect-timeout <duration>` | Connection establishment | 10s |
| `--read-timeout <duration>` | Read/response timeout | 30s |
| `--write-timeout <duration>` | Write/send timeout | 30s |
| `--idle-timeout <duration>` | Idle connection timeout | 60s |
| `--graceful-shutdown-timeout <duration>` | Cleanup time on cancel | 30s |
| `--on-timeout <action>` | Timeout behavior | abort |

<!-- src: audit-agentic-cli/references/execution-patterns.md#Timeout Output -->
## Timeout output

A timeout reports how far it got and how to resume.

```json
{
  "ok": false,
  "error": {
    "class": "timeout",
    "code": "OPERATION_TIMEOUT",
    "message": "Operation timed out after 5m",
    "timeout_type": "overall",
    "elapsed": "5m0.023s",
    "timeout_configured": "5m"
  },
  "partial_result": { "completed_steps": 45, "total_steps": 100, "last_checkpoint": "step-45" },
  "recovery": { "resumable": true, "resume_command": "mycli long-operation --resume-from step-45" }
}
```

<!-- src: audit-agentic-cli/references/execution-patterns.md#Signal Handling -->
## Signal handling

| Signal | Behavior | Exit Code |
|--------|----------|-----------|
| `SIGINT` (Ctrl+C) | Graceful shutdown, attempt cleanup | 130 |
| `SIGTERM` | Graceful shutdown, shorter deadline | 143 |
| `SIGKILL` | Immediate termination (not catchable) | 137 |
| `SIGHUP` | Reload config, continue running | N/A |
| `SIGUSR1` | Dump status/progress | N/A |

The reference grace periods: 30 s after `SIGINT`, 10 s after `SIGTERM`; a second signal forces exit; when the grace period expires the process force-exits with the same signal code (130 or 143), never with 1.

> Reconciled: the signal table says a cancelled run exits 130 or 143, but the Go reference printed `{"ok": true, "status": "cancelled", ...}` and exited 0. A signal-cancelled run exits 130 (SIGINT) or 143 (SIGTERM) and prints `{"ok": false, "status": "cancelled", "cleanup_status": "completed"}`; these signal codes sit beside the 0-8 table in `exit-codes.md`, not in it. A deadline is a different outcome: class `timeout`, exit 7.

<!-- src: audit-agentic-cli/references/execution-patterns.md#Context Cancellation Patterns -->
## Hierarchical timeouts

Nest deadlines so a slow sub-step cannot consume the whole budget:

```
Operation (5m overall)
├── Phase 1: Prepare (30s)
│   ├── Sub-operation A (10s)
│   └── Sub-operation B (10s)
├── Phase 2: Execute (4m)
│   └── Per-item timeout (5s each)
└── Phase 3: Cleanup (30s)
```

Long loops check the context between units of work, clean up when it is cancelled, and return. Implementations (Go context plus signal handler, Python `GracefulShutdown`): `../frameworks/go/execution-patterns-async.md`, `../frameworks/python/execution-patterns-async.md`.

<!-- src: audit-agentic-cli/references/execution-patterns.md#Cancellation Response -->
## Cancellation response

```json
{
  "ok": true,
  "status": "cancelled",
  "completed_before_cancel": 45,
  "total_planned": 100,
  "cleanup_status": "completed",
  "cleanup_details": {
    "rolled_back": ["step-3", "step-2", "step-1"],
    "preserved": ["checkpoint-1"]
  }
}
```

Rollback mechanics: `rollback.md`.
