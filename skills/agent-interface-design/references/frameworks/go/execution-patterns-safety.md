# Go: Dry-Run, Prompts and Rollback

> Read when: you are implementing `--dry-run`, TTY-aware prompts or confirm, or transactional rollback in a Go CLI.

<!-- src: audit-agentic-cli/references/execution-patterns.md#Implementation -->
## Dry-run

Contract: `../../cli/dry-run.md`.

```go
type DryRunMode string

const (
    DryRunNone   DryRunMode = ""
    DryRunClient DryRunMode = "client"
    DryRunServer DryRunMode = "server"
)

type ApplyOptions struct {
    DryRun DryRunMode
    Files  []string
}

type Change struct {
    Action       string            `json:"action"` // create, update, delete
    ResourceType string            `json:"resource_type"`
    ResourceID   string            `json:"resource_id"`
    Diff         map[string]Diff   `json:"diff,omitempty"`
}

type Diff struct {
    Old interface{} `json:"old"`
    New interface{} `json:"new"`
}

type ApplyResult struct {
    OK       bool     `json:"ok"`
    DryRun   bool     `json:"dry_run"`
    Changes  []Change `json:"changes"`
    Summary  Summary  `json:"summary"`
}

func (c *Client) Apply(ctx context.Context, opts ApplyOptions) (*ApplyResult, error) {
    req := ApplyRequest{
        Resources: loadResources(opts.Files),
        DryRun:    opts.DryRun == DryRunServer,
    }

    // Client-side validation
    if opts.DryRun == DryRunClient {
        return c.validateLocally(req.Resources)
    }

    // Send to server
    return c.api.Apply(ctx, req)
}
```

## TTY detection, prompt and confirm

Contract: `../../cli/non-interactive.md`.

> Note: `Confirm` returns a sentinel error that the caller maps to exit 2 (`ExitUsage`), printing a message that names `--yes` / `--force`.

```go
import (
    "bufio"
    "errors"
    "fmt"
    "os"
    "strings"

    "golang.org/x/term"
)

type InteractiveMode int

const (
    ModeAuto InteractiveMode = iota
    ModeInteractive
    ModeNonInteractive
)

var ErrConfirmationRequired = errors.New("confirmation required in non-interactive mode; pass --yes or --force")

func IsInteractive(mode InteractiveMode) bool {
    switch mode {
    case ModeInteractive:
        return true
    case ModeNonInteractive:
        return false
    default:
        // Auto-detect
        return term.IsTerminal(int(os.Stdin.Fd())) &&
               term.IsTerminal(int(os.Stdout.Fd()))
    }
}

func Prompt(message string, mode InteractiveMode) (string, error) {
    if !IsInteractive(mode) {
        return "", fmt.Errorf("prompt required in non-interactive mode (%s): %w", message, ErrConfirmationRequired)
    }

    fmt.Fprint(os.Stderr, message) // prompts go to stderr
    reader := bufio.NewReader(os.Stdin)
    return reader.ReadString('\n')
}

// Caller: if errors.Is(err, ErrConfirmationRequired) { exit(ExitUsage) }
func Confirm(message string, mode InteractiveMode, autoYes bool) (bool, error) {
    if autoYes {
        return true, nil
    }

    if !IsInteractive(mode) {
        return false, ErrConfirmationRequired
    }

    fmt.Fprintf(os.Stderr, "%s [y/N]: ", message)
    reader := bufio.NewReader(os.Stdin)
    response, _ := reader.ReadString('\n')
    return strings.ToLower(strings.TrimSpace(response)) == "y", nil
}
```

<!-- src: audit-agentic-cli/references/execution-patterns.md#Implementation~3 -->
## Transaction with rollback

Contract: `../../cli/rollback.md`.

```go
type Step struct {
    Name    string
    Execute func(ctx context.Context) error
    Undo    func(ctx context.Context) error
}

type Transaction struct {
    steps     []Step
    completed []int
}

func (t *Transaction) AddStep(step Step) {
    t.steps = append(t.steps, step)
}

func (t *Transaction) Execute(ctx context.Context, rollbackOnFailure bool) error {
    for i, step := range t.steps {
        if err := step.Execute(ctx); err != nil {
            if rollbackOnFailure {
                t.Rollback(ctx)
            }
            return fmt.Errorf("step %s failed: %w", step.Name, err)
        }
        t.completed = append(t.completed, i)
    }
    return nil
}

func (t *Transaction) Rollback(ctx context.Context) error {
    // Undo in reverse order
    for i := len(t.completed) - 1; i >= 0; i-- {
        stepIdx := t.completed[i]
        step := t.steps[stepIdx]

        if step.Undo != nil {
            if err := step.Undo(ctx); err != nil {
                // Log but continue rollback
                log.Printf("Rollback step %s failed: %v", step.Name, err)
            }
        }
    }
    return nil
}

// Usage
func Deploy(ctx context.Context) error {
    tx := &Transaction{}

    tx.AddStep(Step{
        Name:    "create-database",
        Execute: func(ctx context.Context) error { return createDatabase(ctx) },
        Undo:    func(ctx context.Context) error { return deleteDatabase(ctx) },
    })

    tx.AddStep(Step{
        Name:    "run-migrations",
        Execute: func(ctx context.Context) error { return runMigrations(ctx) },
        Undo:    func(ctx context.Context) error { return rollbackMigrations(ctx) },
    })

    tx.AddStep(Step{
        Name:    "deploy-application",
        Execute: func(ctx context.Context) error { return deployApp(ctx) },
        Undo:    func(ctx context.Context) error { return rollbackApp(ctx) },
    })

    return tx.Execute(ctx, true) // rollback on failure
}
```
