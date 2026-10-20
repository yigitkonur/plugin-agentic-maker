# Go: Credential Resolution, Refresh and Secret Redaction

> Read when: you are implementing credential lookup, token refresh, log redaction or a git-style credential helper in a Go CLI.

The rules are in `../../cli/auth-and-secrets.md`.

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#Implementation Example~2 -->
## Credential resolution

```go
type AuthStatus struct {
    Authenticated bool      `json:"authenticated"`
    Method        string    `json:"method,omitempty"`
    User          string    `json:"user,omitempty"`
    ExpiresAt     time.Time `json:"expires_at,omitempty"`
    Scopes        []string  `json:"scopes,omitempty"`
    Source        string    `json:"source,omitempty"`
}

func resolveCredentials(cmd *cobra.Command) (string, string, error) {
    // 1. Check CLI flags (secret values come from a file or stdin, never argv)
    if tokenFile, _ := cmd.Flags().GetString("token-file"); tokenFile != "" {
        data, err := os.ReadFile(tokenFile)
        if err != nil {
            return "", "", fmt.Errorf("reading token file: %w", err)
        }
        return strings.TrimSpace(string(data)), "token_file", nil
    }

    if tokenStdin, _ := cmd.Flags().GetBool("token-stdin"); tokenStdin {
        data, err := io.ReadAll(os.Stdin)
        if err != nil {
            return "", "", fmt.Errorf("reading token from stdin: %w", err)
        }
        return strings.TrimSpace(string(data)), "stdin", nil
    }

    // 2. Check environment variable
    if token := os.Getenv("MYCLI_TOKEN"); token != "" {
        return token, "environment_variable", nil
    }

    // 3. Check config (project, then user)
    cfg, err := loadConfig()
    if err == nil && cfg.Token != "" {
        return cfg.Token, "config_file", nil
    }

    // 4. Try credential helper / OS credential store
    if token, err := getFromCredentialHelper(); err == nil {
        return token, "credential_helper", nil
    }

    // 5. Try OIDC / workload identity
    if token, err := getWorkloadIdentityToken(); err == nil {
        return token, "workload_identity", nil
    }

    return "", "", fmt.Errorf("no credentials found") // map to ExitAuth (4)
}
```

> Reconciled: the source also accepted `--token <value>` on the command line, which exposes the secret in the process list; this file drops that branch and keeps `--token-file` and `--token-stdin`.

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#Token Refresh -->
## Token refresh

```go
func getAuthenticatedClient(ctx context.Context) (*Client, error) {
    token, source, err := resolveCredentials()
    if err != nil {
        return nil, err
    }

    // Check if token is expired and refreshable
    if isExpired(token) {
        refreshToken, err := getRefreshToken(source)
        if err != nil {
            return nil, fmt.Errorf("token expired and no refresh token: %w", err)
        }

        newToken, err := refreshAccessToken(ctx, refreshToken)
        if err != nil {
            return nil, fmt.Errorf("token refresh failed: %w", err)
        }

        // Store new token
        if err := storeToken(source, newToken); err != nil {
            // Log but don't fail - token works for this request
            log.Printf("warning: failed to store refreshed token: %v", err)
        }

        token = newToken
    }

    return NewClient(token), nil
}
```

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#Implementation Example~5 -->
## Redaction and credential helper

```go
// Redact sensitive fields in logs
func redactSensitive(v interface{}) interface{} {
    switch val := v.(type) {
    case map[string]interface{}:
        result := make(map[string]interface{})
        for k, v := range val {
            if isSensitiveKey(k) {
                result[k] = "***REDACTED***"
            } else {
                result[k] = redactSensitive(v)
            }
        }
        return result
    case []interface{}:
        result := make([]interface{}, len(val))
        for i, v := range val {
            result[i] = redactSensitive(v)
        }
        return result
    default:
        return v
    }
}

func isSensitiveKey(key string) bool {
    sensitive := []string{"password", "token", "secret", "key", "credential", "auth"}
    lower := strings.ToLower(key)
    for _, s := range sensitive {
        if strings.Contains(lower, s) {
            return true
        }
    }
    return false
}

// Git-style credential helper support
func getFromCredentialHelper() (string, error) {
    helper := os.Getenv("MYCLI_CREDENTIAL_HELPER")
    if helper == "" {
        helper = "mycli-credential-helper"
    }

    cmd := exec.Command(helper, "get")
    cmd.Stdin = strings.NewReader("host=api.example.com\nprotocol=https\n")

    output, err := cmd.Output()
    if err != nil {
        return "", err
    }

    // Parse credential helper output
    for _, line := range strings.Split(string(output), "\n") {
        if strings.HasPrefix(line, "password=") {
            return strings.TrimPrefix(line, "password="), nil
        }
    }

    return "", fmt.Errorf("no password in credential helper output")
}
```
