# Go: Testing JSON Output

> Read when: you need a table-driven Go test that runs the CLI and checks exit code, `ok`, and envelope fields.

<!-- src: audit-agentic-cli/references/examples.md#16.1 Unit Testing JSON Output (Go) -->
## Unit testing JSON output

The cases follow the skeleton in `examples.md` (`resource create`, `resource list`); the `get` and `delete` cases assume the same group has those subcommands, so adapt the argument lists to your CLI.

```go
package main

import (
    "bytes"
    "encoding/json"
    "os/exec"
    "strings"
    "testing"
)

func TestJSONOutput(t *testing.T) {
    tests := []struct {
        name       string
        args       []string
        wantOK     bool
        wantFields map[string]any
        wantExit   int
    }{
        {
            name:     "create success",
            args:     []string{"resource", "create", "test-resource", "--json"},
            wantOK:   true,
            wantExit: 0,
            wantFields: map[string]any{
                "result.name": "test-resource",
            },
        },
        {
            name:     "get not found",
            args:     []string{"resource", "get", "nonexistent", "--json"},
            wantOK:   false,
            wantExit: 3,
            wantFields: map[string]any{
                "error.class": "not_found",
                "error.code":  "RESOURCE_NOT_FOUND",
            },
        },
        {
            name:     "delete without confirmation",
            args:     []string{"resource", "delete", "res_123", "--json"},
            wantOK:   false,
            wantExit: 2,
            wantFields: map[string]any{
                "error.class": "usage",
            },
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            cmd := exec.Command("./mycli", tt.args...)
            var stdout, stderr bytes.Buffer
            cmd.Stdout = &stdout
            cmd.Stderr = &stderr

            err := cmd.Run()

            // Check exit code
            exitCode := 0
            if exitErr, ok := err.(*exec.ExitError); ok {
                exitCode = exitErr.ExitCode()
            }
            if exitCode != tt.wantExit {
                t.Errorf("exit code = %d, want %d", exitCode, tt.wantExit)
            }

            // The envelope, success or failure, is on stdout; stderr is never JSON
            var resp map[string]any
            if err := json.Unmarshal(stdout.Bytes(), &resp); err != nil {
                t.Fatalf("invalid JSON: %v\nstdout: %s\nstderr: %s", err, stdout.Bytes(), stderr.Bytes())
            }

            // Check ok field
            if ok, _ := resp["ok"].(bool); ok != tt.wantOK {
                t.Errorf("ok = %v, want %v", ok, tt.wantOK)
            }

            // Check expected fields (simplified path lookup)
            for path, want := range tt.wantFields {
                got := lookupPath(resp, path)
                if got != want {
                    t.Errorf("%s = %v, want %v", path, got, want)
                }
            }
        })
    }
}

func lookupPath(m map[string]any, path string) any {
    // Simplified: split by "." and traverse
    parts := strings.Split(path, ".")
    var current any = m
    for _, part := range parts {
        if cm, ok := current.(map[string]any); ok {
            current = cm[part]
        } else {
            return nil
        }
    }
    return current
}
```

> Reconciled: the source fell back to stderr when stdout was empty; the envelope is always on stdout, so this test reads stdout only. It also adds the missing `strings` import.
