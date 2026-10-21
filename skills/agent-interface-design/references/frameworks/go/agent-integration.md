# Go: Calling a CLI from an Agent

> Read when: you are writing the Go side that runs a CLI with `os/exec`: JSON invocation, timeouts, retry with backoff, and JSONL streaming with context cancellation.

The rules are in `../../cli/caller-integration.md`. Streaming rules are in `../../cli/streams-and-jsonl.md`.

<!-- src: audit-agentic-cli/references/agent-integration.md#11. Go Integration | audit-agentic-cli/references/agent-integration.md#Basic os/exec Invocation -->
## Basic os/exec invocation

```go
package agent

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"os/exec"
	"time"
)

// CLIResult represents structured CLI output
type CLIResult struct {
	OK     bool            `json:"ok"`
	Result json.RawMessage `json:"result,omitempty"`
	Error  *CLIError       `json:"error,omitempty"`
}

type CLIError struct {
	Class      string `json:"class"`
	Code       string `json:"code"`
	Message    string `json:"message"`
	Retryable  bool   `json:"retryable"`
	Suggestion string `json:"suggestion,omitempty"`
}

// InvokeCLI executes a CLI command with JSON output and timeout
func InvokeCLI(ctx context.Context, args []string, timeout time.Duration) (*CLIResult, error) {
	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	// Append standard flags
	fullArgs := append(args, "--json", "--quiet")
	cmd := exec.CommandContext(ctx, fullArgs[0], fullArgs[1:]...)

	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	cmd.Env = append(cmd.Environ(), "NO_COLOR=1")

	err := cmd.Run()
	if ctx.Err() == context.DeadlineExceeded {
		return &CLIResult{
			OK:    false,
			Error: &CLIError{Class: "timeout", Code: "timeout", Message: "Command timed out", Retryable: true},
		}, nil
	}
	if ctx.Err() != nil { // cancelled by the caller: not a CLI failure, not retryable
		return nil, ctx.Err()
	}

	if stdout.Len() > 0 {
		var result CLIResult
		if err := json.Unmarshal(stdout.Bytes(), &result); err != nil {
			return nil, fmt.Errorf("invalid JSON output: %w", err)
		}
		return &result, nil
	}

	if err != nil {
		exitCode := 1
		if exitErr, ok := err.(*exec.ExitError); ok {
			exitCode = exitErr.ExitCode()
		}
		return &CLIResult{
			OK:    false,
			Error: &CLIError{Code: fmt.Sprintf("exit_%d", exitCode), Message: stderr.String(), Retryable: exitCode == 7}, // exit 7 = transient
		}, nil
	}

	return &CLIResult{OK: true}, nil
}
```

<!-- src: audit-agentic-cli/references/agent-integration.md#Context Cancellation and Retry -->
## Context cancellation and retry

```go
package agent

import (
	"context"
	"math"
	"math/rand"
	"time"
)

// InvokeWithRetry executes CLI with exponential backoff retry
func InvokeWithRetry(ctx context.Context, args []string, opts RetryOptions) (*CLIResult, error) {
	if opts.MaxRetries == 0 {
		opts.MaxRetries = 3
	}
	if opts.BaseDelay == 0 {
		opts.BaseDelay = time.Second
	}

	if opts.Timeout == 0 {
		opts.Timeout = 30 * time.Second
	}

	var lastResult *CLIResult
	for attempt := 0; attempt <= opts.MaxRetries; attempt++ {
		result, err := InvokeCLI(ctx, args, opts.Timeout)
		if err != nil {
			return nil, err
		}

		if result.OK {
			return result, nil
		}

		lastResult = result
		if result.Error == nil || !result.Error.Retryable {
			return result, nil
		}

		if attempt == opts.MaxRetries {
			break
		}

		// Exponential backoff with jitter
		delay := opts.BaseDelay * time.Duration(math.Pow(2, float64(attempt)))
		jitter := time.Duration(rand.Float64() * float64(time.Second))

		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		case <-time.After(delay + jitter):
		}
	}

	return lastResult, nil
}

type RetryOptions struct {
	MaxRetries int
	BaseDelay  time.Duration
	Timeout    time.Duration
}
```

<!-- src: audit-agentic-cli/references/agent-integration.md#JSONL Streaming with Context -->
## JSONL streaming with context

```go
package agent

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"os/exec"
	"time"
)

// TaskEvent represents a streaming task event
type TaskEvent struct {
	Type   string          `json:"type"`
	TaskID string          `json:"task_id,omitempty"`
	Data   json.RawMessage `json:"data,omitempty"`
}

// StreamTaskEvents streams JSONL events from task follow
func StreamTaskEvents(ctx context.Context, taskID string) (<-chan TaskEvent, <-chan error) {
	events := make(chan TaskEvent)
	errs := make(chan error, 1)

	go func() {
		defer close(events)
		defer close(errs)

		cmd := exec.CommandContext(ctx, "mycli", "task", "follow", taskID, "--json")
		stdout, err := cmd.StdoutPipe()
		if err != nil {
			errs <- err
			return
		}

		if err := cmd.Start(); err != nil {
			errs <- err
			return
		}

		scanner := bufio.NewScanner(stdout)
		for scanner.Scan() {
			var event TaskEvent
			if err := json.Unmarshal(scanner.Bytes(), &event); err != nil {
				continue // Skip malformed lines
			}
			select {
			case events <- event:
			case <-ctx.Done():
				cmd.Process.Kill()
				return
			}
		}

		if err := scanner.Err(); err != nil {
			errs <- err
			return
		}
		if err := cmd.Wait(); err != nil && ctx.Err() == nil {
			errs <- fmt.Errorf("mycli task follow: %w", err) // the CLI's own non-zero exit
		}
	}()

	return events, errs
}

// Usage example
func RunTaskWithStreaming(ctx context.Context, promptFile string) error {
	// Start task
	result, err := InvokeCLI(ctx, []string{"mycli", "task", "start", promptFile}, 30*time.Second)
	if err != nil || !result.OK {
		if err == nil {
			err = fmt.Errorf("%s: %s", result.Error.Code, result.Error.Message)
		}
		return fmt.Errorf("failed to start task: %w", err)
	}

	var startResp struct {
		TaskID string `json:"task_id"`
	}
	json.Unmarshal(result.Result, &startResp)

	// Stream events; cancel on return so the follower process stops
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()
	events, errs := StreamTaskEvents(ctx, startResp.TaskID)
	for {
		select {
		case event, ok := <-events:
			if !ok { // the follower ended without a "complete" event: say why, never report success
				if err := <-errs; err != nil { // nil on a clean close
					return err
				}
				if ctx.Err() != nil {
					return ctx.Err()
				}
				return fmt.Errorf("stream ended without a complete event")
			}
			switch event.Type {
			case "approval":
				// Never auto-approve: ask the operator, then run `mycli request answer <id> --yes`
				return fmt.Errorf("approval needed: %s", event.Data)
			case "complete":
				return nil
			case "error":
				return fmt.Errorf("task error: %s", event.Data)
			}
		case err := <-errs:
			if err != nil {
				return err
			}
		case <-ctx.Done():
			return ctx.Err()
		}
	}
}
```
