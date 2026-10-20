# Go: Operations, Wait/Stream, Timeouts and Signals

> Read when: you are implementing submit/poll/wait/stream commands, an overall timeout or SIGINT/SIGTERM handling in Go.

<!-- src: audit-agentic-cli/references/execution-patterns.md#Implementation~4 -->
## Operation status, wait and stream

Contract: `../../cli/async-and-long-running.md`.

```go
type Operation struct {
    ID        string         `json:"operation_id"`
    Status    string         `json:"status"` // accepted, running, succeeded, failed, cancelled
    Progress  *Progress      `json:"progress,omitempty"`
    Result    interface{}    `json:"result,omitempty"`
    Error     *ErrorInfo     `json:"error,omitempty"`
    StartedAt time.Time      `json:"started_at"`
    UpdatedAt time.Time      `json:"updated_at"`
}

type Progress struct {
    Phase   string `json:"phase"`
    Percent int    `json:"percent"`
    Message string `json:"message"`
}

// emit writes one JSON value to w (stdout for data, stderr for progress events).
func emit(w io.Writer, v interface{}) error { return json.NewEncoder(w).Encode(v) }

// opExit: `task wait` exits 0 only for a succeeded operation, so an agent never reads a failed deploy as success.
func opExit(op *Operation) int {
    switch op.Status {
    case "succeeded":
        return ExitSuccess
    case "cancelled":
        return ExitPartial // ran, did not complete; the envelope's status says why
    default: // failed: map op.Error.Class with the switch in exitWithError (discovery-and-auth.md)
        return ExitCrash
    }
}

// CLI commands return the exit code to os.Exit in main.
func cmdTaskStatus(operationID string) (int, error) {
    op, err := api.GetOperation(operationID)
    if err != nil {
        return 0, err
    }
    return 0, emit(os.Stdout, op)
}

func cmdTaskWait(operationID string, timeout time.Duration) (int, error) {
    ctx, cancel := context.WithTimeout(context.Background(), timeout)
    defer cancel()

    ticker := time.NewTicker(2 * time.Second)
    defer ticker.Stop()

    for {
        select {
        case <-ctx.Done():
            return 0, fmt.Errorf("waiting for operation: %w", ErrTimeout) // exit 7
        case <-ticker.C:
            op, err := api.GetOperation(operationID)
            if err != nil {
                return 0, err
            }

            switch op.Status {
            case "succeeded", "failed", "cancelled":
                return opExit(op), emit(os.Stdout, op)
            }
            // Continue polling
        }
    }
}

// Progress events go to stderr, the terminal event to stdout
// (../../cli/streams-and-jsonl.md).
func cmdDeployStream() (int, error) {
    ctx := context.Background()

    op, err := api.StartDeploy(ctx)
    if err != nil {
        return 0, err
    }

    stream, err := api.StreamOperation(ctx, op.ID)
    if err != nil {
        return 0, err
    }

    for event := range stream {
        if event.Type == "completed" { // terminal event; status says succeeded, failed or cancelled
            return opExit(&Operation{Status: event.Status}), emit(os.Stdout, event)
        }
        emit(os.Stderr, event)
    }
    return 0, fmt.Errorf("stream ended without a terminal event: %w", ErrUnavailable) // exit 7: retryable
}
```

<!-- src: audit-agentic-cli/references/execution-patterns.md#Implementation~5 -->
## Timeout context and signal handling

Contract: `../../cli/timeouts-and-signals.md`. A deadline exits 7 with class `timeout`; a signal cancels the run, prints a `cancelled` envelope and exits 130 (SIGINT) or 143 (SIGTERM).

```go
func main() {
    flags := parseFlags()
    ctx, cancel := context.WithTimeout(context.Background(), flags.timeout) // e.g. 5 * time.Minute
    defer cancel()

    var received atomic.Value // the signal that cancelled the run, if any
    sigCh := make(chan os.Signal, 2)
    signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

    go func() {
        sig := <-sigCh
        log.Printf("Received signal: %v", sig) // stderr
        received.Store(sig)
        cancel() // start graceful shutdown

        grace := 30 * time.Second // SIGINT
        if sig == syscall.SIGTERM {
            grace = 10 * time.Second
        }
        select {
        case <-sigCh: // a second signal forces exit
        case <-time.After(grace):
        }
        log.Println("Grace period expired, forcing exit")
        os.Exit(signalExit(sig)) // 130 or 143, never 1
    }()

    err := run(ctx)
    switch {
    case err == nil:
        return
    case errors.Is(err, context.DeadlineExceeded):
        emit(os.Stdout, map[string]interface{}{"ok": false, "error": map[string]interface{}{
            "class": "timeout", "code": "OPERATION_TIMEOUT", "message": "operation timed out", "retryable": true}})
        os.Exit(ExitTransient) // 7
    case errors.Is(err, context.Canceled):
        sig, _ := received.Load().(os.Signal)
        emit(os.Stdout, map[string]interface{}{"ok": false, "status": "cancelled", "cleanup_status": "completed"})
        os.Exit(signalExit(sig))
    default:
        exitWithError(err, flags.json) // the table in discovery-and-auth.md, not log.Fatal
    }
}

func signalExit(sig os.Signal) int {
    if sig == syscall.SIGTERM {
        return 143
    }
    return 130
}

func run(ctx context.Context) error {
    // Long-running operation that respects context cancellation
    for i := 0; i < 100; i++ {
        select {
        case <-ctx.Done():
            // Cleanup
            cleanup()
            return ctx.Err()
        default:
            // Continue work
            doWork(i)
        }
    }
    return nil
}
```
