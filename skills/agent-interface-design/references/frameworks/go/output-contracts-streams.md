# Go: Stream Separation and JSONL Emitters

> Read when: you are writing the stdout/stderr split, verbose logging or JSONL event emitters in Go.

<!-- src: audit-agentic-cli/references/output-contracts.md#Implementation Examples -->
## JSONL emitters

Contract: `../../cli/streams-and-jsonl.md`. Flush after each line; one object per line.

```go
package main

import (
    "encoding/json"
    "fmt"
    "os"
    "time"
)

type ProgressEvent struct {
    Type      string    `json:"type"`
    Phase     string    `json:"phase"`
    Percent   int       `json:"percent,omitempty"`
    Message   string    `json:"message,omitempty"`
    Timestamp time.Time `json:"timestamp"`
}

type CompletedEvent struct {
    Type   string      `json:"type"`
    Status string      `json:"status"`
    Result interface{} `json:"result"`
}

// Progress is not a result: it goes to stderr (still one JSON object per line).
func emitProgress(phase string, percent int, message string) {
    event := ProgressEvent{
        Type:      "progress",
        Phase:     phase,
        Percent:   percent,
        Message:   message,
        Timestamp: time.Now().UTC(),
    }
    data, _ := json.Marshal(event)
    fmt.Fprintln(os.Stderr, string(data))
    os.Stderr.Sync() // Flush immediately
}

// The terminal event is a result: it goes to stdout, as the last line.
func emitCompleted(result interface{}) {
    event := CompletedEvent{
        Type:   "completed",
        Status: "succeeded",
        Result: result,
    }
    data, _ := json.Marshal(event)
    fmt.Fprintln(os.Stdout, string(data))
}
```

> Reconciled: the source wrote `emitProgress` to `os.Stdout`; progress events go to stderr per the stream rule.

<!-- src: audit-agentic-cli/references/output-contracts.md#Never Do This -->
## Never do this

```go
// BAD: Mixing human text with JSON in stdout
fmt.Println("Creating resource...")  // Goes to stdout
data, _ := json.Marshal(result)
fmt.Println(string(data))            // Also stdout — can't parse!
```

<!-- src: audit-agentic-cli/references/output-contracts.md#Do This Instead -->
## Do this instead

```go
// GOOD: Separate streams
fmt.Fprintln(os.Stderr, "Creating resource...")  // Human text to stderr
data, _ := json.Marshal(result)
fmt.Fprintln(os.Stdout, string(data))            // JSON to stdout
```

## Verbose levels

Verbose output goes to stderr only.

```go
var verboseLevel int

func log(level int, msg string) {
    if level <= verboseLevel {
        fmt.Fprintln(os.Stderr, msg)
    }
}

// Usage:
// -v     → verboseLevel 1 (info)
// -vv    → verboseLevel 2 (debug)
// -vvv   → verboseLevel 3 (trace)
```

<!-- src: audit-agentic-cli/references/output-contracts.md#Complete Example -->
## Complete example

Progress to stderr; the envelope, success or failure, once to stdout; the exit code from the table.

```go
package main

import (
    "encoding/json"
    "fmt"
    "os"
)

func main() {
    // Progress to stderr
    fmt.Fprintln(os.Stderr, "Connecting to server...")

    result, err := doOperation()
    if err != nil {
        // Error JSON to stdout (for --json mode)
        response := map[string]interface{}{
            "ok": false,
            "error": map[string]interface{}{
                "class":   "network",
                "code":    "CONNECTION_FAILED",
                "message": err.Error(),
            },
        }
        json.NewEncoder(os.Stdout).Encode(response)
        os.Exit(7) // TRANSIENT
    }

    // Success JSON to stdout
    response := map[string]interface{}{
        "ok":     true,
        "result": result,
    }
    json.NewEncoder(os.Stdout).Encode(response)
    os.Exit(0)
}
```
