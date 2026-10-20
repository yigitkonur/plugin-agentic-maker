# Go: Environment Detection

> Read when: you are implementing CI, TTY, shell and colour detection, and deriving prompt and output behaviour from it, in a Go CLI.

The rules are in `../../cli/config-and-env.md`.

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#Implementation Example~6 -->
## Detect the environment

```go
type Environment struct {
    OS           string  `json:"os"`
    Arch         string  `json:"arch"`
    Terminal     bool    `json:"terminal"`
    CI           bool    `json:"ci"`
    CIPlatform   *string `json:"ci_platform"`
    Shell        string  `json:"shell"`
    ColorSupport bool    `json:"color_support"`
}

func detectEnvironment() *Environment {
    env := &Environment{
        OS:       runtime.GOOS,
        Arch:     runtime.GOARCH,
        Terminal: isTerminal(os.Stdout),
        CI:       isCI(),
        Shell:    detectShell(),
    }

    if env.CI {
        env.CIPlatform = detectCIPlatform()
    }

    env.ColorSupport = shouldUseColor(env)

    return env
}

func isTerminal(f *os.File) bool {
    fi, err := f.Stat()
    if err != nil {
        return false
    }
    return fi.Mode()&os.ModeCharDevice != 0
}

func isCI() bool {
    ciVars := []string{"CI", "GITHUB_ACTIONS", "GITLAB_CI", "JENKINS_URL", "CIRCLECI", "TRAVIS"}
    for _, v := range ciVars {
        if os.Getenv(v) != "" {
            return true
        }
    }
    return false
}

func detectCIPlatform() *string {
    platforms := map[string]string{
        "GITHUB_ACTIONS": "github_actions",
        "GITLAB_CI":      "gitlab",
        "JENKINS_URL":    "jenkins",
        "CIRCLECI":       "circleci",
        "TRAVIS":         "travis",
    }

    for env, name := range platforms {
        if os.Getenv(env) != "" {
            return &name
        }
    }
    return nil
}

func shouldUseColor(env *Environment) bool {
    // NO_COLOR takes precedence
    if os.Getenv("NO_COLOR") != "" {
        return false
    }

    // FORCE_COLOR overrides
    if os.Getenv("FORCE_COLOR") != "" {
        return true
    }

    // CI or non-terminal: no color by default
    if env.CI || !env.Terminal {
        return false
    }

    // Check TERM
    term := os.Getenv("TERM")
    return term != "" && term != "dumb"
}

func detectShell() string {
    shell := os.Getenv("SHELL")
    if shell == "" {
        return "unknown"
    }
    return filepath.Base(shell)
}
```

## Use it in a command

```go
func runCommand(cmd *cobra.Command, args []string) error {
    env := detectEnvironment()

    // Configure output based on environment
    output := &OutputConfig{
        JSON:     jsonFlag || !env.Terminal,
        Color:    env.ColorSupport && !jsonFlag,
        Progress: env.Terminal && !env.CI,
        Prompts:  env.Terminal && !env.CI && !nonInteractive,
    }

    // If non-interactive mode, fail on any required input
    if !output.Prompts {
        if needsUserInput(args) {
            // exit 2, naming the flag that supplies the answer
            return usageError("confirmation required: pass --yes (or --force), or provide all required flags")
        }
    }

    // Execute with configured output
    return executeWithOutput(ctx, output, args)
}
```

> Reconciled: the source returned a generic error here; this file returns a usage error (exit 2) naming the flag.
