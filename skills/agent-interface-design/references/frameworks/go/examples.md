# Go: Structured Output, Exit Codes and a Cobra Skeleton

> Read when: you need working Go code for the JSON envelope helpers, error constructors with exit codes, and a complete Cobra CLI skeleton.

Conventions shared with the other stacks: `../../cli/implementation-conventions.md`. Batch and progress: `examples-batch-and-progress.md`. Tests: `examples-tests.md`.

<!-- src: audit-agentic-cli/references/examples.md#1. Structured Output (Go) -->
## Structured output

```go
package main

import (
    "encoding/json"
    "fmt"
    "os"
)

type Response struct {
    OK            bool        `json:"ok"`
    Command       string      `json:"command,omitempty"`
    SchemaVersion string      `json:"schema_version"`
    Result  interface{} `json:"result,omitempty"`
    Error   *ErrorInfo  `json:"error,omitempty"`
    Meta    *Meta       `json:"meta,omitempty"`
}

type ErrorInfo struct {
    Class      string      `json:"class"`
    Code       string      `json:"code"`
    Message    string      `json:"message"`
    Retryable  bool        `json:"retryable"`
    Suggestion string      `json:"suggestion,omitempty"`
    Details    interface{} `json:"details,omitempty"`
}

type Meta struct {
    Truncated  bool `json:"truncated,omitempty"`
    TotalCount int  `json:"total_count,omitempty"`
    DurationMs int  `json:"duration_ms,omitempty"`
}

// The envelope, success and failure, goes to stdout.
func outputJSON(resp Response) {
    resp.SchemaVersion = "1.0"
    enc := json.NewEncoder(os.Stdout)
    enc.SetIndent("", "  ")
    enc.Encode(resp)
}

func success(result interface{}) {
    outputJSON(Response{OK: true, Result: result})
    os.Exit(0)
}

// jsonOutput is the --json flag (declared in the skeleton below).
func fail(class, code, message string, retryable bool, exitCode int) {
    fmt.Fprintln(os.Stderr, message) // the human diagnostic, always on stderr
    if jsonOutput {                  // the envelope, once, on stdout
        outputJSON(Response{
            OK: false,
            Error: &ErrorInfo{
                Class:     class,
                Code:      code,
                Message:   message,
                Retryable: retryable,
            },
        })
    }
    os.Exit(exitCode)
}
```

<!-- src: audit-agentic-cli/references/examples.md#4. Exit Code Handling (Go) -->
## Exit code handling

```go
package main

import (
    "fmt"
    "os"
)

// Exit codes as constants
const (
    ExitSuccess    = 0 // Success
    ExitCrash      = 1 // Unexpected/internal error
    ExitUsage      = 2 // Usage/input error
    ExitNotFound   = 3 // Resource not found
    ExitAuth       = 4 // Auth/permission denied
    ExitConflict   = 5 // Conflict/already exists
    ExitValidation = 6 // Validation error
    ExitTransient  = 7 // Retryable error: rate_limit, timeout, network, dependency_failed
    ExitPartial    = 8 // Some operations succeeded, some failed
)

type AppError struct {
    Class     string
    Code      string
    Message   string
    Retryable bool
    ExitCode  int
}

func (e *AppError) Exit() {
    fail(e.Class, e.Code, e.Message, e.Retryable, e.ExitCode)
}

// Factory functions
func ErrNotFound(resource string) *AppError {
    return &AppError{
        Class:     "not_found",
        Code:      "RESOURCE_NOT_FOUND",
        Message:   fmt.Sprintf("Resource '%s' not found", resource),
        Retryable: false,
        ExitCode:  ExitNotFound,
    }
}

func ErrConflict(resource string) *AppError {
    return &AppError{
        Class:     "conflict",
        Code:      "RESOURCE_EXISTS",
        Message:   fmt.Sprintf("Resource '%s' already exists", resource),
        Retryable: false,
        ExitCode:  ExitConflict,
    }
}

func ErrTransient(message string) *AppError {
    return &AppError{
        Class:     "network", // transient is the exit-7 group; the class is network/timeout/rate_limit/dependency_failed
        Code:      "NETWORK_ERROR",
        Message:   message,
        Retryable: true,
        ExitCode:  ExitTransient,
    }
}
```

> Note: exit 1 is `ExitCrash`, the exit-7 example uses class `network` with code `NETWORK_ERROR`, and `ExitPartial = 8` completes the 0-8 table.

<!-- src: audit-agentic-cli/references/examples.md#10. Complete CLI Skeleton (Go with Cobra) -->
## Complete CLI skeleton

```go
package main

import (
    "encoding/json"
    "fmt"
    "os"

    "github.com/spf13/cobra"
)

var (
    jsonOutput     bool
    quiet          bool
    nonInteractive bool
    yes            bool
    force          bool
    timeout        string
)

func main() {
    rootCmd := &cobra.Command{
        Use:   "mycli",
        Short: "Agent-friendly CLI example",
    }

    // Global flags
    rootCmd.PersistentFlags().BoolVar(&jsonOutput, "json", false, "Output as JSON")
    rootCmd.PersistentFlags().BoolVarP(&quiet, "quiet", "q", false, "Minimal output")
    rootCmd.PersistentFlags().BoolVar(&nonInteractive, "non-interactive", false, "Fail on prompts")
    rootCmd.PersistentFlags().BoolVarP(&yes, "yes", "y", false, "Auto-confirm")
    rootCmd.PersistentFlags().BoolVarP(&force, "force", "f", false, "Force operation")
    rootCmd.PersistentFlags().StringVar(&timeout, "timeout", "30s", "Operation timeout")

    // Resource subcommand
    resourceCmd := &cobra.Command{Use: "resource", Short: "Manage resources"}

    resourceCmd.AddCommand(&cobra.Command{
        Use:   "create <name>",
        Short: "Create a new resource",
        Args:  cobra.ExactArgs(1),
        Run:   createResource,
    })

    resourceCmd.AddCommand(&cobra.Command{
        Use:   "list",
        Short: "List all resources",
        Run:   listResources,
    })

    rootCmd.AddCommand(resourceCmd)

    if err := rootCmd.Execute(); err != nil {
        fail("usage", "USAGE_ERROR", err.Error(), false, ExitUsage) // cobra rejected the command line: exit 2, envelope in --json mode
    }
}

func createResource(cmd *cobra.Command, args []string) {
    name := args[0]

    // Check for conflict
    if exists(name) && !force {
        fail("conflict", "RESOURCE_EXISTS",
            fmt.Sprintf("Resource '%s' already exists", name), false, ExitConflict)
    }

    resource := create(name)

    if jsonOutput {
        outputJSON(Response{OK: true, Command: "resource create", Result: resource})
    } else if quiet {
        fmt.Println(resource.ID)
    } else {
        fmt.Printf("Created resource: %s\n", resource.ID)
    }
}

// A minimal in-memory store so the skeleton is complete; replace it with the real API.
type Resource struct {
    ID   string `json:"id"`
    Name string `json:"name"`
}

var store = map[string]Resource{}

func exists(name string) bool { _, ok := store[name]; return ok }

func create(name string) Resource {
    r := Resource{ID: "res_" + name, Name: name}
    store[name] = r
    return r
}

func listResources(cmd *cobra.Command, args []string) {
    items := make([]Resource, 0, len(store))
    for _, r := range store {
        items = append(items, r)
    }
    if jsonOutput {
        outputJSON(Response{OK: true, Command: "resource list", Result: map[string]any{"items": items}})
        return
    }
    for _, r := range items {
        fmt.Println(r.ID)
    }
}
```

> Note: when Cobra rejects the command line the program exits 2 (`ExitUsage`); conflicts use `ExitConflict`.
