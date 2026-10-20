# Go: Bulk Create and Bounded-Concurrency Batches

> Read when: you are implementing chunked bulk operations with partial-failure reporting and failure thresholds in Go.

<!-- src: audit-agentic-cli/references/execution-patterns.md#Implementation~2 -->
## Bulk create with partial failure

Contract: `../../cli/batch-and-partial.md`. The final status is `success`, `partial_failure` or `failed` (`cancelled` when the context ends first); the process exit for `partial_failure` is 8 (`ExitPartial`). Read-only and idempotent batches default to continue; destructive batches default to stop (`StopOnError`).

```go
type BulkOptions struct {
    ChunkSize       int
    Concurrency     int
    ContinueOnError bool
    StopOnError     bool
}

type BulkResult struct {
    OK        bool         `json:"ok"`
    Status    string       `json:"status"` // success, partial_failure, failed
    Summary   BulkSummary  `json:"summary"`
    Succeeded []ItemResult `json:"succeeded"`
    Failed    []ItemError  `json:"failed"`
}

func BulkCreate(ctx context.Context, items []Item, opts BulkOptions) (*BulkResult, error) {
    ctx, cancel := context.WithCancel(ctx) // StopOnError cancels the rest of the batch
    defer cancel()
    result := &BulkResult{
        Succeeded: make([]ItemResult, 0),
        Failed:    make([]ItemError, 0),
    }

    // Process in chunks
    chunks := chunkItems(items, opts.ChunkSize)

    for _, chunk := range chunks {
        // Process chunk with concurrency limit
        sem := make(chan struct{}, opts.Concurrency)
        var wg sync.WaitGroup
        var mu sync.Mutex

        for _, item := range chunk {
            if ctx.Err() != nil {
                break
            }

            sem <- struct{}{}
            wg.Add(1)

            go func(item Item) {
                defer wg.Done()
                defer func() { <-sem }()

                res, err := createItem(ctx, item)

                mu.Lock()
                defer mu.Unlock()

                if err != nil {
                    result.Failed = append(result.Failed, ItemError{
                        ID:    item.ID,
                        Error: classifyError(err),
                    })

                    if opts.StopOnError {
                        cancel() // items not yet started see ctx.Err() and are skipped
                    }
                } else {
                    result.Succeeded = append(result.Succeeded, res)
                }
            }(item)
        }

        wg.Wait()

        if opts.StopOnError && len(result.Failed) > 0 {
            break
        }
    }

    // Set final status
    result.Summary = BulkSummary{
        Total:     len(items),
        Succeeded: len(result.Succeeded),
        Failed:    len(result.Failed),
    }

    if len(result.Failed) == 0 {
        result.OK = true
        result.Status = "success"
    } else if len(result.Succeeded) > 0 {
        result.OK = false
        result.Status = "partial_failure"
    } else {
        result.OK = false
        result.Status = "failed"
    }

    return result, nil
}
```

<!-- src: audit-agentic-cli/references/execution-patterns.md#Implementation~7 -->
## Bounded concurrency with a semaphore

Contract: `../../cli/batch-limits.md`.

```go
type BatchOptions struct {
    BatchSize            int           `json:"batch_size"`
    MaxConcurrent        int           `json:"max_concurrent"`
    DelayBetweenBatches  time.Duration `json:"delay_between_batches"`
    MaxItems             int           `json:"max_items"`
    ContinueOnError      bool          `json:"continue_on_error"`
    FailThreshold        float64       `json:"fail_threshold"`
    RetryFailed          int           `json:"retry_failed"`
}

type BatchResult struct {
    OK        bool                `json:"ok"`
    Status    string              `json:"status"`
    Summary   BatchSummary        `json:"summary"`
    Timing    BatchTiming         `json:"timing"`
    Succeeded []ItemResult        `json:"succeeded,omitempty"`
    Failed    []ItemFailure       `json:"failed,omitempty"`
    Recovery  *RecoveryInfo       `json:"recovery,omitempty"`
}

func ProcessBatch(ctx context.Context, items []Item, opts BatchOptions) (*BatchResult, error) {
    ctx, cancel := context.WithCancel(ctx) // the fail threshold cancels the rest of the batch
    defer cancel()
    if opts.MaxItems > 0 && len(items) > opts.MaxItems {
        items = items[:opts.MaxItems]
    }

    result := &BatchResult{
        Summary: BatchSummary{TotalInput: len(items)},
    }
    startTime := time.Now()

    // Create semaphore for concurrency control
    sem := make(chan struct{}, opts.MaxConcurrent)
    var mu sync.Mutex
    var wg sync.WaitGroup

    // Split into batches
    batches := chunkItems(items, opts.BatchSize)

    for batchIdx, batch := range batches {
        select {
        case <-ctx.Done():
            wg.Wait() // let running goroutines finish writing to result before it is returned
            result.Status = "cancelled"
            return result, ctx.Err()
        default:
        }

        // Delay between batches
        if batchIdx > 0 && opts.DelayBetweenBatches > 0 {
            time.Sleep(opts.DelayBetweenBatches)
        }

        for itemIdx, item := range batch {
            wg.Add(1)
            sem <- struct{}{} // Acquire

            go func(item Item, bIdx, iIdx int) {
                defer wg.Done()
                defer func() { <-sem }() // Release

                // Process with retry
                var lastErr error
                for attempt := 0; attempt <= opts.RetryFailed; attempt++ {
                    if err := processItem(ctx, item); err != nil {
                        lastErr = err
                        if !isRetryable(err) {
                            break
                        }
                        time.Sleep(backoff(attempt))
                        continue
                    }

                    mu.Lock()
                    result.Succeeded = append(result.Succeeded, ItemResult{ID: item.ID})
                    result.Summary.Succeeded++
                    mu.Unlock()
                    return
                }

                mu.Lock()
                result.Failed = append(result.Failed, ItemFailure{
                    ID:         item.ID,
                    BatchIndex: bIdx,
                    ItemIndex:  iIdx,
                    Error:      toErrorInfo(lastErr),
                })
                result.Summary.Failed++

                // Check fail threshold
                failRate := float64(result.Summary.Failed) / float64(result.Summary.Processed())
                mu.Unlock()

                if !opts.ContinueOnError || failRate > opts.FailThreshold {
                    cancel() // the loop above sees ctx.Done() and stops dispatching
                }
            }(item, batchIdx, itemIdx)
        }
    }

    wg.Wait()

    result.Timing.Elapsed = time.Since(startTime)
    result.OK = result.Summary.Failed == 0
    result.Status = determineStatus(result.Summary)

    // Generate recovery info if failures
    if len(result.Failed) > 0 {
        result.Recovery = generateRecoveryInfo(result.Failed)
    }

    return result, nil
}
```
