# Go: Exit Codes, Field Selection, Pagination, Quiet Mode

> Read when: you are implementing the output contract of a Go CLI (exit constants, class mapping, `--fields`, pagination struct, `--quiet`).

<!-- src: audit-agentic-cli/references/output-contracts.md#Exit Code Constants -->
## Exit code constants

Define constants to avoid magic numbers. The table they implement is `../../cli/exit-codes.md`.

```go
// exitcodes.go
const (
    ExitSuccess    = 0  // Operation completed successfully
    ExitCrash      = 1  // Unexpected error, internal failure
    ExitUsage      = 2  // Bad flags, invalid arguments
    ExitNotFound   = 3  // Resource does not exist
    ExitAuth       = 4  // Authentication/authorization failed
    ExitConflict   = 5  // Resource conflict (exists, version mismatch)
    ExitValidation = 6  // Input validation failed
    ExitTransient  = 7  // Retryable error (network, timeout, rate limit)
    ExitPartial    = 8  // Partial success (some operations failed)
)
```

<!-- src: audit-agentic-cli/references/output-contracts.md#Mapping Classes to Exit Codes -->
## Mapping classes to exit codes

> Reconciled: the source used `ExitAuthDenied` here and `ExitError` for the default, neither defined by the constants above, and had no case for `usage`, `dependency_failed` or `partial_success`. This file uses `ExitAuth`, `ExitCrash` as the default, and maps the missing classes per `../../cli/error-classes.md`.

```go
func errorClassToExitCode(class string) int {
    switch class {
    case "usage":
        return ExitUsage
    case "not_found":
        return ExitNotFound
    case "conflict":
        return ExitConflict
    case "validation":
        return ExitValidation
    case "auth":
        return ExitAuth
    case "rate_limit", "timeout", "network", "dependency_failed":
        return ExitTransient
    case "partial_success":
        return ExitPartial
    case "internal":
        return ExitCrash
    default:
        return ExitCrash
    }
}
```

<!-- src: audit-agentic-cli/references/output-contracts.md#Implementation -->
## Field selection

For `--fields id,name,status` (`../../cli/field-selection.md`):

```go
func filterFields(data map[string]interface{}, fields []string) map[string]interface{} {
    if len(fields) == 0 {
        return data
    }
    result := make(map[string]interface{})
    for _, field := range fields {
        if val, ok := data[field]; ok {
            result[field] = val
        }
    }
    return result
}
```

<!-- src: audit-agentic-cli/references/output-contracts.md#Implementation~2 -->
## Pagination structs

> Reconciled: the source used a `PaginationInfo` sibling with `Total`, `Page`, `PerPage`, `HasMore`, `NextCursor` and a bare-array `Result`. The field names below follow `../../cli/pagination.md`: `result.items`, `result.next_cursor`, `result.has_more`, optional `result.total`.

```go
type PageResult[T any] struct {
    Items      []T    `json:"items"`
    Total      int    `json:"total,omitempty"`
    PerPage    int    `json:"per_page"`
    HasMore    bool   `json:"has_more"`
    NextCursor string `json:"next_cursor,omitempty"`
}

type PaginatedResponse[T any] struct {
    OK     bool    `json:"ok"`
    Result PageResult[T] `json:"result"`
}
```

<!-- src: audit-agentic-cli/references/output-contracts.md#Implementation~3 -->
## Quiet mode

```go
var quietFlag bool

func init() {
    rootCmd.PersistentFlags().BoolVarP(&quietFlag, "quiet", "q", false,
        "Minimal output suitable for pipelines")
}

func outputResult(id string, full interface{}) {
    if jsonFlag { // the envelope, once, even with --quiet
        data, _ := json.MarshalIndent(full, "", "  ")
        fmt.Println(string(data))
        return
    }
    if quietFlag {
        fmt.Println(id)
        return
    }
    // Human-readable output
    fmt.Printf("Created resource: %s\n", id)
}
```

Note: `MarshalIndent` pretty-prints; that is fine for a single envelope but not for JSONL stream mode (`../../cli/streams-and-jsonl.md`).
