# Go/Cobra: Flags, Exit Codes, Help and Version

> Read when: you are implementing the standard flags, the exit-code mapping, self-documenting help or `version --json` in a Go CLI built on Cobra.

The rules are in `../../cli/discovery-and-help.md` and `../../cli/exit-codes.md`. Credentials: `discovery-and-auth-credentials.md`; config and providers: `discovery-and-auth-config.md`; environment: `discovery-and-auth-env.md`.

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#Implementation Pattern -->
## Standard flags

```go
// Add standard flags to root command
func addStandardFlags(cmd *cobra.Command) {
    cmd.PersistentFlags().BoolP("json", "j", false, "Output as JSON")
    cmd.PersistentFlags().BoolP("quiet", "q", false, "Suppress non-essential output")
    cmd.PersistentFlags().BoolP("verbose", "v", false, "Increase verbosity")
    cmd.PersistentFlags().BoolP("yes", "y", false, "Skip confirmations")
    cmd.PersistentFlags().Bool("dry-run", false, "Preview without executing")
    cmd.PersistentFlags().BoolP("force", "f", false, "Override safety checks")
    cmd.PersistentFlags().StringP("output", "o", "table", "Output format: json|yaml|table|text")
    cmd.PersistentFlags().Duration("timeout", 30*time.Second, "Operation timeout")
    cmd.PersistentFlags().Bool("no-input", false, "Non-interactive mode")
}
```

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#Implementation Pattern~2 -->
## Exit codes and error mapping

```go
const (
    ExitSuccess    = 0
    ExitCrash      = 1
    ExitUsage      = 2
    ExitNotFound   = 3
    ExitAuth       = 4
    ExitConflict   = 5
    ExitValidation = 6
    ExitTransient  = 7
    ExitPartial    = 8
)

// exitWithError maps an error to the exit table and, in --json mode, prints the failure envelope
// once on stdout (../../cli/envelope-and-errors.md); the human line always goes to stderr.
func exitWithError(err error, jsonMode bool) {
    code, class := ExitCrash, "internal"
    switch {
    case errors.Is(err, ErrNotFound):
        code, class = ExitNotFound, "not_found"
    case errors.Is(err, ErrUnauthorized), errors.Is(err, ErrForbidden):
        code, class = ExitAuth, "auth"
    case errors.Is(err, ErrConflict), errors.Is(err, ErrAlreadyExists):
        code, class = ExitConflict, "conflict"
    case errors.Is(err, ErrValidation), errors.Is(err, ErrInvalidInput):
        code, class = ExitValidation, "validation"
    case errors.Is(err, ErrTimeout):
        code, class = ExitTransient, "timeout"
    case errors.Is(err, ErrRateLimit):
        code, class = ExitTransient, "rate_limit"
    case errors.Is(err, ErrUnavailable):
        code, class = ExitTransient, "dependency_failed"
    case errors.Is(err, ErrPartial):
        code, class = ExitPartial, "partial_success"
    case errors.Is(err, ErrUsage):
        code, class = ExitUsage, "usage"
    case errors.Is(err, context.Canceled):
        code = 130 // SIGINT stop; a SIGTERM stop exits 143 (../../cli/timeouts-and-signals.md)
    }
    fmt.Fprintln(os.Stderr, err)
    if jsonMode {
        json.NewEncoder(os.Stdout).Encode(map[string]interface{}{
            "ok": false, "schema_version": "1.0",
            "error": map[string]interface{}{
                "class": class, "code": strings.ToUpper(class), "message": err.Error(),
                "retryable": code == ExitTransient,
            },
        })
    }
    os.Exit(code)
}
```

> Reconciled: the sources named the auth constant `ExitAuthDenied` in one file and `ExitAuth` in another, and stopped at 7; this file uses `ExitAuth` and adds `ExitPartial = 8` (and an `ErrPartial` case) for the 0-8 table.

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#Implementation Example (Go/Cobra) -->
## Help with examples

```go
var deployCmd = &cobra.Command{
    Use:   "deploy <service-name>",
    Short: "Deploy a service to the target environment",
    Long: `Deploy a service to the target environment.

Supports dry-run mode for previewing changes and JSON output
for integration with automation tools.`,
    Args: cobra.ExactArgs(1),
    Example: `  # Deploy to staging
  mycli deploy web-api --env staging

  # Deploy specific image to production
  mycli deploy web-api --env prod --image myregistry/web:v2.1.0 --json

  # Preview deployment changes
  mycli deploy web-api --env dev --dry-run`,
    RunE: runDeploy,
}

func init() {
    deployCmd.Flags().StringP("env", "e", "", "Target environment: dev, staging, prod (required)")
    deployCmd.Flags().String("image", "", "Container image override")
    deployCmd.Flags().Int("replicas", 0, "Number of replicas")
    deployCmd.Flags().Bool("dry-run", false, "Preview changes without applying")
    deployCmd.Flags().Bool("wait", true, "Wait for deployment to complete")
    deployCmd.Flags().Duration("timeout", 5*time.Minute, "Maximum wait time")
    // --json is the root persistent flag; do not redeclare it here (a local copy shadows -j)

    deployCmd.MarkFlagRequired("env")
}
```

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#Implementation Example -->
## Version and capabilities

```go
type VersionInfo struct {
    Version      string   `json:"version"`
    GitCommit    string   `json:"git_commit"`
    BuildDate    string   `json:"build_date"`
    GoVersion    string   `json:"go_version"`
    Capabilities []string `json:"capabilities"`
    APIVersion   string   `json:"api_version"`
}

var versionCmd = &cobra.Command{
    Use:   "version",
    Short: "Print version and build information",
    RunE: func(cmd *cobra.Command, args []string) error {
        info := VersionInfo{
            Version:      Version,
            GitCommit:    GitCommit,
            BuildDate:    BuildDate,
            GoVersion:    runtime.Version(),
            Capabilities: []string{"streaming", "batch", "dry-run-server"},
            APIVersion:   "v2",
        }

        if jsonOutput, _ := cmd.Flags().GetBool("json"); jsonOutput {
            return json.NewEncoder(os.Stdout).Encode(map[string]interface{}{
                "ok": true, "command": "version", "schema_version": "1.0",
                "result": info, "meta": map[string]interface{}{},
            })
        }

        fmt.Printf("mycli %s (commit: %s, built: %s)\n",
            info.Version, info.GitCommit, info.BuildDate)
        return nil
    },
}
```
