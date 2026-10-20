# Go: Idempotency Keys, Retry and Circuit Breaker

> Read when: you are implementing idempotent creates, retry with backoff or a circuit breaker in a Go CLI or its API client.

## Idempotency key handler

Contract: `../../cli/idempotency.md`. Cached results live 24 hours; errors are not cached.

```go
type CreateRequest struct {
    Name           string `json:"name"`
    IdempotencyKey string `json:"idempotency_key,omitempty"`
}

func (s *Server) handleCreate(w http.ResponseWriter, r *http.Request) {
    var req CreateRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        writeError(w, fmt.Errorf("invalid request body: %w", ErrValidation)) // exit 6 class
        return
    }

    // Check idempotency cache
    if req.IdempotencyKey != "" {
        if cached, ok := s.idempotencyCache.Get(req.IdempotencyKey); ok {
            json.NewEncoder(w).Encode(cached)
            return
        }
    }

    // Perform creation
    result, err := s.createResource(req)
    if err != nil {
        // Don't cache errors (except for specific cases)
        writeError(w, err)
        return
    }

    // Cache successful result
    if req.IdempotencyKey != "" {
        s.idempotencyCache.Set(req.IdempotencyKey, result, 24*time.Hour)
    }

    json.NewEncoder(w).Encode(result)
}
```

<!-- src: audit-agentic-cli/references/execution-patterns.md#Go Retry Implementation -->
## Retry

Contract and defaults: `../../cli/retry.md`.

```go
package retry

import (
    "context"
    "errors"
    "fmt"
    "math"
    "math/rand"
    "net/http"
    "strconv"
    "sync"
    "time"
)

type Config struct {
    MaxAttempts     int
    InitialBackoff  time.Duration
    MaxBackoff      time.Duration
    BackoffFactor   float64
    Jitter          float64 // 0.0 to 1.0
}

var DefaultConfig = Config{
    MaxAttempts:    5,
    InitialBackoff: 100 * time.Millisecond,
    MaxBackoff:     30 * time.Second,
    BackoffFactor:  2.0,
    Jitter:         0.2,
}

type RetryableError struct {
    Err        error
    RetryAfter time.Duration
}

func (e *RetryableError) Error() string { return e.Err.Error() }
func (e *RetryableError) Unwrap() error { return e.Err }

func IsRetryable(err error) bool {
    var retryErr *RetryableError
    return errors.As(err, &retryErr)
}

func Do(ctx context.Context, cfg Config, operation func() error) error {
    var lastErr error

    for attempt := 0; attempt < cfg.MaxAttempts; attempt++ {
        err := operation()
        if err == nil {
            return nil
        }

        lastErr = err

        // Check if retryable
        var retryErr *RetryableError
        if !errors.As(err, &retryErr) {
            return err // Non-retryable, fail immediately
        }

        // Check context
        if ctx.Err() != nil {
            return ctx.Err()
        }

        if attempt == cfg.MaxAttempts-1 {
            break // no sleep before giving up
        }

        // Calculate backoff
        var backoff time.Duration
        if retryErr.RetryAfter > 0 {
            backoff = retryErr.RetryAfter
        } else {
            backoff = cfg.InitialBackoff * time.Duration(math.Pow(cfg.BackoffFactor, float64(attempt)))
            if backoff > cfg.MaxBackoff {
                backoff = cfg.MaxBackoff
            }
            // Add jitter
            jitter := time.Duration(float64(backoff) * cfg.Jitter * (rand.Float64()*2 - 1))
            backoff += jitter
        }

        select {
        case <-time.After(backoff):
            continue
        case <-ctx.Done():
            return ctx.Err()
        }
    }

    return fmt.Errorf("max retries exceeded: %w: %w", ErrUnavailable, lastErr) // exit 7
}

// HTTP client with retry
func DoHTTP(ctx context.Context, client *http.Client, req *http.Request) (*http.Response, error) {
    var resp *http.Response

    err := Do(ctx, DefaultConfig, func() error {
        if resp != nil {
            resp.Body.Close() // the previous 429/5xx response is abandoned
        }
        r := req.Clone(ctx)
        if req.GetBody != nil { // Clone shares Body, which a first attempt consumed
            r.Body, _ = req.GetBody()
        }
        var err error
        resp, err = client.Do(r)
        if err != nil {
            return &RetryableError{Err: err}
        }

        switch resp.StatusCode {
        case http.StatusTooManyRequests:
            retryAfter := parseRetryAfter(resp.Header.Get("Retry-After"))
            return &RetryableError{
                Err:        fmt.Errorf("rate limited"),
                RetryAfter: retryAfter,
            }
        case http.StatusServiceUnavailable, http.StatusBadGateway, http.StatusGatewayTimeout:
            return &RetryableError{Err: fmt.Errorf("server error: %d", resp.StatusCode)}
        case http.StatusConflict:
            // Not retried: the table says conflict is "No (check details)". Re-read and decide, then start a new operation.
            return fmt.Errorf("conflict: %w", ErrConflict) // exit 5
        default:
            if resp.StatusCode >= 500 {
                return &RetryableError{Err: fmt.Errorf("server error: %d", resp.StatusCode)}
            }
            return nil // Success or client error (not retryable)
        }
    })

    return resp, err
}

func parseRetryAfter(value string) time.Duration {
    if value == "" {
        return 0
    }
    // Try seconds
    if seconds, err := strconv.Atoi(value); err == nil {
        return time.Duration(seconds) * time.Second
    }
    // Try HTTP date
    if t, err := http.ParseTime(value); err == nil {
        return time.Until(t)
    }
    return 0
}
```

## Circuit breaker

Stop retrying after repeated failures (`../../cli/retry.md`).

```go
type CircuitBreaker struct {
    maxFailures   int
    resetTimeout  time.Duration
    failures      int
    lastFailure   time.Time
    state         string // "closed", "open", "half-open"
    mu            sync.Mutex
}

func (cb *CircuitBreaker) Execute(operation func() error) error {
    cb.mu.Lock()

    // Check if circuit is open
    if cb.state == "open" {
        if time.Since(cb.lastFailure) > cb.resetTimeout {
            cb.state = "half-open"
        } else {
            cb.mu.Unlock()
            return fmt.Errorf("circuit breaker open: %w", ErrUnavailable) // exit 7
        }
    }
    cb.mu.Unlock()

    err := operation()

    cb.mu.Lock()
    defer cb.mu.Unlock()

    if err != nil {
        cb.failures++
        cb.lastFailure = time.Now()
        if cb.failures >= cb.maxFailures {
            cb.state = "open"
        }
        return err
    }

    // Success - reset
    cb.failures = 0
    cb.state = "closed"
    return nil
}
```
