# Go: Cursor Pagination and Rate Limiter

> Read when: you are implementing cursor pagination or a token-bucket rate limiter with circuit breaker in Go.

<!-- src: audit-agentic-cli/references/execution-patterns.md#Implementation~6 -->
## Cursor pagination

Contract: `../../cli/pagination.md`.

> Reconciled: the source returned `Data` and a `PageInfo` with `TotalCount`, `HasNext`, `PageSize`. The names below follow `result.items`, `result.next_cursor`, `result.has_more`, optional `result.total`.

```go
type PaginationOptions struct {
    PerPage   int    `json:"per_page"`
    Cursor    string `json:"cursor,omitempty"`
    Page      int    `json:"page,omitempty"`
    All       bool   `json:"all,omitempty"`
    MaxPages  int    `json:"max_pages,omitempty"`
    SortBy    string `json:"sort_by,omitempty"`
    SortOrder string `json:"sort_order,omitempty"`
}

type PageResult[T any] struct {
    Items      []T    `json:"items"`
    Total      int    `json:"total,omitempty"`
    PerPage    int    `json:"per_page"`
    HasMore    bool   `json:"has_more"`
    NextCursor string `json:"next_cursor,omitempty"`
}

type PaginatedResponse[T any] struct {
    OK     bool          `json:"ok"`
    Result PageResult[T] `json:"result"`
}

func (s *Server) ListItems(ctx context.Context, opts PaginationOptions) (*PaginatedResponse[Item], error) {
    // Decode cursor if provided
    var startAfter *Item
    if opts.Cursor != "" {
        decoded, err := decodeCursor(opts.Cursor)
        if err != nil {
            return nil, fmt.Errorf("invalid cursor: %w", err)
        }
        startAfter = decoded
    }

    // Fetch one extra to determine has_more
    limit := opts.PerPage + 1
    items, err := s.db.QueryItems(ctx, startAfter, limit, opts.SortBy, opts.SortOrder)
    if err != nil {
        return nil, err
    }

    hasMore := len(items) > opts.PerPage
    if hasMore {
        items = items[:opts.PerPage]
    }

    var nextCursor string
    if hasMore && len(items) > 0 {
        nextCursor = encodeCursor(items[len(items)-1])
    }

    return &PaginatedResponse[Item]{
        OK: true,
        Result: PageResult[Item]{
            Items:      items,
            PerPage:    opts.PerPage,
            HasMore:    hasMore,
            NextCursor: nextCursor,
        },
    }, nil
}

// Cursor encoding/decoding
func encodeCursor(item *Item) string {
    data, _ := json.Marshal(map[string]interface{}{
        "id":         item.ID,
        "created_at": item.CreatedAt,
    })
    return base64.URLEncoding.EncodeToString(data)
}

func decodeCursor(cursor string) (*Item, error) {
    data, err := base64.URLEncoding.DecodeString(cursor)
    if err != nil {
        return nil, err
    }
    var item Item
    if err := json.Unmarshal(data, &item); err != nil {
        return nil, err
    }
    return &item, nil
}
```

<!-- src: audit-agentic-cli/references/execution-patterns.md#Implementation~8 -->
## Rate limiter with circuit breaker

Contract: `../../cli/rate-limits.md`.

```go
type RateLimitOptions struct {
    RateLimit             string        `json:"rate_limit"` // e.g., "100/minute"
    RetryOnRateLimit      bool          `json:"retry_on_rate_limit"`
    MaxRetries            int           `json:"max_retries"`
    BackoffInitial        time.Duration `json:"backoff_initial"`
    BackoffMax            time.Duration `json:"backoff_max"`
    BackoffMultiplier     float64       `json:"backoff_multiplier"`
    BackoffJitter         float64       `json:"backoff_jitter"`
    RespectRetryAfter     bool          `json:"respect_retry_after"`
    CircuitBreakerThreshold int         `json:"circuit_breaker_threshold"`
    CircuitBreakerTimeout time.Duration `json:"circuit_breaker_timeout"`
}

type RateLimiter struct {
    limiter       *rate.Limiter
    opts          RateLimitOptions
    failures      int
    circuitOpen   bool
    circuitOpenAt time.Time
    mu            sync.Mutex
}

func NewRateLimiter(opts RateLimitOptions) (*RateLimiter, error) {
    limit, err := parseRateLimit(opts.RateLimit) // e.g., "100/minute" -> rate.Limit
    if err != nil {
        return nil, err
    }

    return &RateLimiter{
        limiter: rate.NewLimiter(limit, int(limit)), // burst = limit
        opts:    opts,
    }, nil
}

func (r *RateLimiter) Do(ctx context.Context, fn func() (*http.Response, error)) (*http.Response, error) {
    // Check circuit breaker
    r.mu.Lock()
    if r.circuitOpen {
        if time.Since(r.circuitOpenAt) > r.opts.CircuitBreakerTimeout {
            r.circuitOpen = false
            r.failures = 0
        } else {
            r.mu.Unlock()
            return nil, &CircuitOpenError{
                OpenAt:  r.circuitOpenAt,
                WaitFor: r.opts.CircuitBreakerTimeout - time.Since(r.circuitOpenAt),
            }
        }
    }
    r.mu.Unlock()

    // Wait for rate limit
    if err := r.limiter.Wait(ctx); err != nil {
        return nil, err
    }

    var lastErr error
    backoff := r.opts.BackoffInitial

    for attempt := 0; attempt <= r.opts.MaxRetries; attempt++ {
        resp, err := fn()
        if err != nil {
            lastErr = err
            r.recordFailure()
            continue
        }

        // Handle rate limit response
        if resp.StatusCode == http.StatusTooManyRequests {
            r.recordFailure()

            if !r.opts.RetryOnRateLimit {
                return resp, nil
            }

            // Determine wait time
            waitTime := backoff
            if r.opts.RespectRetryAfter {
                if retryAfter := resp.Header.Get("Retry-After"); retryAfter != "" {
                    if seconds, err := strconv.Atoi(retryAfter); err == nil {
                        waitTime = time.Duration(seconds) * time.Second
                    } else if t, err := http.ParseTime(retryAfter); err == nil {
                        waitTime = time.Until(t)
                    }
                }
            }

            // Add jitter
            if r.opts.BackoffJitter > 0 {
                jitter := time.Duration(float64(waitTime) * r.opts.BackoffJitter * (rand.Float64()*2 - 1))
                waitTime += jitter
            }

            select {
            case <-ctx.Done():
                return nil, ctx.Err()
            case <-time.After(waitTime):
            }

            // Exponential backoff for next attempt
            backoff = time.Duration(float64(backoff) * r.opts.BackoffMultiplier)
            if backoff > r.opts.BackoffMax {
                backoff = r.opts.BackoffMax
            }

            lastErr = &RateLimitError{RetryAfter: waitTime}
            continue
        }

        // Success - reset failures
        r.recordSuccess()
        return resp, nil
    }

    return nil, fmt.Errorf("max retries exceeded: %w", lastErr)
}

func (r *RateLimiter) recordFailure() {
    r.mu.Lock()
    defer r.mu.Unlock()

    r.failures++
    if r.failures >= r.opts.CircuitBreakerThreshold {
        r.circuitOpen = true
        r.circuitOpenAt = time.Now()
    }
}

func (r *RateLimiter) recordSuccess() {
    r.mu.Lock()
    defer r.mu.Unlock()
    r.failures = 0
    r.circuitOpen = false
}
```
