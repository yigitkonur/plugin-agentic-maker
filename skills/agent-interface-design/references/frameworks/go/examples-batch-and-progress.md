# Go: Batch with Partial Failure and Long-Running Progress

> Read when: you need Go code for a concurrent batch that collects per-item errors, or for a long-running task that reports progress as JSONL.

Rules: `../../cli/caller-integration.md` (batches), `../../cli/streams-and-jsonl.md` (JSONL), `../../cli/exit-codes.md` (partial is exit 8).

<!-- src: audit-agentic-cli/references/examples.md#6. Batch Operations with Partial Failure (Go) -->
## Batch operations with partial failure

```go
package main

import (
    "context"
    "sync"
)

type BatchConfig struct {
    ChunkSize       int
    Concurrency     int
    ContinueOnError bool
}

type BatchResult struct {
    Total     int          `json:"total"`
    Succeeded int          `json:"succeeded"`
    Failed    int          `json:"failed"`
    Errors    []BatchError `json:"errors,omitempty"`
    mu        sync.Mutex
}

type BatchError struct {
    ID    string `json:"id"`
    Error string `json:"error"`
    Class string `json:"class"`
}

func (r *BatchResult) addSuccess() {
    r.mu.Lock()
    r.Succeeded++
    r.mu.Unlock()
}

func (r *BatchResult) addError(id, errClass, errMsg string) {
    r.mu.Lock()
    r.Failed++
    r.Errors = append(r.Errors, BatchError{
        ID:    id,
        Error: errMsg,
        Class: errClass,
    })
    r.mu.Unlock()
}

func BatchProcess(ctx context.Context, items []Item, cfg BatchConfig, process func(Item) error) *BatchResult {
    result := &BatchResult{Total: len(items)}

    sem := make(chan struct{}, cfg.Concurrency)
    var wg sync.WaitGroup

    for _, item := range items {
        if ctx.Err() != nil {
            break
        }

        sem <- struct{}{}
        wg.Add(1)

        go func(item Item) {
            defer wg.Done()
            defer func() { <-sem }()

            if err := process(item); err != nil {
                result.addError(item.ID, classifyError(err), err.Error())
                if !cfg.ContinueOnError {
                    // Signal to stop (via context cancellation in real impl)
                }
            } else {
                result.addSuccess()
            }
        }(item)
    }

    wg.Wait()
    return result
}
```

> Reconciled: the source did not say what `ContinueOnError` defaults to. Read-only and idempotent batches default to continue and report partial (exit 8, never 3); destructive batches default to stop at the first error. `--stop-on-error` / `--continue-on-error` override either. When `Succeeded > 0` and `Failed > 0`, exit with `ExitPartial`.

<!-- src: audit-agentic-cli/references/examples.md#9. Long-Running Task with Progress (Go) -->
## Long-running task with progress

```go
package main

import (
    "context"
    "encoding/json"
    "os"
    "time"
)

type TaskStatus struct {
    OperationID string     `json:"operation_id"`
    Status      string     `json:"status"`
    Progress    *Progress  `json:"progress,omitempty"`
    Result      any        `json:"result,omitempty"`
    Error       *ErrorInfo `json:"error,omitempty"`
    StartedAt   time.Time  `json:"started_at"`
    CompletedAt *time.Time `json:"completed_at,omitempty"`
}

type Progress struct {
    Phase   string `json:"phase"`
    Percent int    `json:"percent"`
    Message string `json:"message,omitempty"`
}

func runWithProgress(ctx context.Context, opID string, work func(progress chan<- Progress) error) {
    progressCh := make(chan Progress, 10)
    resultCh := make(chan error, 1)

    // Worker goroutine
    go func() {
        resultCh <- work(progressCh)
        close(progressCh)
    }()

    progressEnc := json.NewEncoder(os.Stderr) // progress is not a result
    resultEnc := json.NewEncoder(os.Stdout)   // terminal events are results

    // Progress reporter
    for {
        select {
        case p, ok := <-progressCh:
            if !ok {
                return
            }
            progressEnc.Encode(map[string]any{
                "type":         "progress",
                "operation_id": opID,
                "phase":        p.Phase,
                "percent":      p.Percent,
                "message":      p.Message,
            })

        case err := <-resultCh:
            if err != nil {
                resultEnc.Encode(map[string]any{
                    "type":         "error",
                    "operation_id": opID,
                    "error":        err.Error(),
                })
            } else {
                resultEnc.Encode(map[string]any{
                    "type":         "completed",
                    "operation_id": opID,
                    "status":       "succeeded",
                })
            }
            return

        case <-ctx.Done():
            resultEnc.Encode(map[string]any{
                "type":         "cancelled",
                "operation_id": opID,
            })
            return
        }
    }
}
```

> Reconciled: the source wrote every event, including `error`, `completed` and `cancelled`, to stderr. This file writes progress to stderr and the terminal events (results) to stdout; never mix them on one stream.
