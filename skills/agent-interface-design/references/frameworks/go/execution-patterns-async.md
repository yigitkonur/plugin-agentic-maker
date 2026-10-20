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

// CLI commands
func cmdTaskStatus(operationID string) error {
    op, err := api.GetOperation(operationID)
    if err != nil {
        return err
    }
    return outputJSON(op)
}

func cmdTaskWait(operationID string, timeout time.Duration) error {
    ctx, cancel := context.WithTimeout(context.Background(), timeout)
    defer cancel()

    ticker := time.NewTicker(2 * time.Second)
    defer ticker.Stop()

    for {
        select {
        case <-ctx.Done():
            return fmt.Errorf("timeout waiting for operation")
        case <-ticker.C:
            op, err := api.GetOperation(operationID)
            if err != nil {
                return err
            }

            switch op.Status {
            case "succeeded":
                return outputJSON(op)
            case "failed":
                return outputJSON(op)
            case "cancelled":
                return outputJSON(op)
            }
            // Continue polling
        }
    }
}

// Progress events go to stderr, the terminal event to stdout
// (../../cli/streams-and-jsonl.md). outputJSON here writes to stdout.
func cmdDeployStream() error {
    ctx := context.Background()

    // Start operation
    op, err := api.StartDeploy(ctx)
    if err != nil {
        return err
    }

    // Stream progress
    stream, err := api.StreamOperation(ctx, op.ID)
    if err != nil {
        return err
    }

    for event := range stream {
        if event.Type == "completed" || event.Type == "failed" {
            outputJSON(event)
            break
        }
        outputJSONTo(os.Stderr, event)
    }

    return nil
}
```

<!-- src: audit-agentic-cli/references/execution-patterns.md#Implementation~5 -->
## Timeout context and signal handling

Contract: `../../cli/timeouts-and-signals.md`. The unresolved exit code after a signal is recorded there; this sample prints a `cancelled` result and exits 0 as the source did.

```go
func main() {
    // Parse timeout flags
    timeout := parseFlags().timeout // e.g., 5 * time.Minute
    gracePeriod := parseFlags().gracefulShutdownTimeout // e.g., 30 * time.Second

    // Create timeout context
    ctx, cancel := context.WithTimeout(context.Background(), timeout)
    defer cancel()

    // Handle signals
    sigCh := make(chan os.Signal, 1)
    signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

    go func() {
        sig := <-sigCh
        log.Printf("Received signal: %v", sig)

        // Start graceful shutdown
        cancel()

        // Force exit after grace period
        var gracePeriod time.Duration
        if sig == syscall.SIGTERM {
            gracePeriod = 10 * time.Second
        } else {
            gracePeriod = 30 * time.Second
        }

        time.Sleep(gracePeriod)
        log.Println("Grace period expired, forcing exit")
        os.Exit(1)
    }()

    // Run main operation
    if err := run(ctx); err != nil {
        if ctx.Err() == context.Canceled {
            outputJSON(map[string]interface{}{
                "ok":             true,
                "status":         "cancelled",
                "cleanup_status": "completed",
            })
            os.Exit(0)
        }
        log.Fatal(err)
    }
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
