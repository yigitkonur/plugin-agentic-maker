# Auth and Secrets

> Read when: you are designing or auditing how a CLI obtains, orders, stores and reports credentials for headless and agent use.

Go code for credential resolution, refresh, redaction and the credential helper is in `../frameworks/go/discovery-and-auth-credentials.md`. Exit 4 is the auth exit code (`exit-codes.md`).

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#4. Authentication Patterns | audit-agentic-cli/references/discovery-and-auth.md#Credential Resolution Order | audit-agentic-cli/references/discovery-and-auth.md#Credential Resolution Flow -->
## Credential precedence

Resolve credentials in this order, first hit wins:

1. Flag: `--token-file <path>` or `--token-stdin`. Never a secret value on argv.
2. Environment variable (`MYCLI_TOKEN`).
3. Project config.
4. User config.
5. OS credential store (keychain or a git-credential-style helper).
6. Workload identity (OIDC): on a cloud host, get the identity token from the metadata API and exchange it for an API token.
7. Interactive login (`mycli auth login`): human bootstrap only, and only with a TTY. Without a TTY, fail with exit 4 "no credentials" naming the sources that were checked.

Decision flow after a credential is found:

```
credential found?
  no  -> TTY? yes: prompt "mycli auth login" | no: exit 4
  yes -> token valid?
           yes -> authenticated
           expired + refreshable -> refresh -> ok: authenticated | fail: exit 4
           no  -> exit 4
```

> Reconciled: the sources gave three orders (flag, env, config file, keychain, OIDC, interactive; a flowchart with a credential helper after config; and stdin, file, flag, env, config, keychain, OIDC). This file uses flag (never a secret value on argv: use `--token-file` or stdin), then environment variable, project config, user config, OS credential store; workload identity and interactive login come after those.

> Unresolved: the sources list "config file has token" as a credential source and also forbid secrets in plaintext config files. Both claims are kept: treat a config layer as a legitimate source, but a CLI that stores a raw secret there in plaintext is the finding.

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#Authentication Flow Diagrams | audit-agentic-cli/references/discovery-and-auth.md#Token-Based Authentication -->
## Token login flow

`mycli auth login --token-stdin`, token piped on stdin:

1. The CLI validates the token format.
2. It calls `GET /auth/validate`; the API answers `200 OK` with user info.
3. It stores the token in the credential store.
4. It confirms: "Authenticated as user@example.com".
5. Later requests (`mycli resource list`) read the token from the store and send `Authorization: Bearer <token>`.

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#OAuth 2.0 Device Flow (Headless/CI) -->
## OAuth 2.0 device flow (headless)

1. `mycli auth login`: the CLI posts to `/device/code` and receives `device_code`, `user_code`, `verification_uri`.
2. It prints the URL (`https://auth.example.com/device`) and the code (`ABCD-1234`) on stderr for the human.
3. The human opens the URL in a browser, enters the code and approves.
4. The CLI polls `POST /token` with the `device_code` every 5 s. The answer is `authorization_pending` until it becomes an `access_token`.
5. The CLI stores the tokens and confirms "Authenticated as user@example.com".

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#Service Account / Workload Identity -->
## Service account / workload identity

1. The CLI detects that it runs inside a cloud environment.
2. It requests `GET /instance/service-accounts/default/token` from the metadata API and receives a cloud identity token.
3. It posts that token to the token-exchange endpoint (`POST /token`) and receives an API access token.
4. It calls the API with `Authorization: Bearer <api_access_token>`.
5. It refreshes the token before expiry, without prompting.

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#Secure Credential Handling -->
## Secure credential handling

```bash
# GOOD: stdin (no process list exposure)
echo "$TOKEN" | mycli auth login --token-stdin

# GOOD: file (no process list exposure)
mycli auth login --token-file /path/to/token

# ACCEPTABLE: env var
MYCLI_TOKEN=xxx mycli deploy

# BAD: command line argument (visible in ps)
mycli auth login --token secret123  # AVOID
```

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#Auth Status -->
## Auth status

`mycli auth status --json` answers "which credential am I using and when does it die", without printing the secret:

```json
{
  "authenticated": true,
  "method": "oauth",
  "user": "alice@example.com",
  "expires_at": "2024-01-16T10:00:00Z",
  "scopes": ["read", "write"],
  "source": "config_file"
}
```

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#Token Refresh -->
## Token refresh

Refresh transparently. If the token is expired but refreshable, refresh it before the operation. If the refresh token is missing or the refresh fails, fail with exit 4. If storing the refreshed token fails, log a warning and carry on: the new token works for this request.

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#7. Secret Handling Rules | audit-agentic-cli/references/discovery-and-auth.md#Never | audit-agentic-cli/references/discovery-and-auth.md#Always -->
## Secret handling rules

Never:

- Accept secrets as command-line arguments.
- Print secrets to stdout or stderr.
- Store secrets in plaintext config files.
- Log secrets at any level.

Always:

- Use stdin or a file for secret input.
- Redact secrets in logs (`***REDACTED***`). Treat keys containing `password`, `token`, `secret`, `key`, `credential` or `auth` as sensitive, case-insensitively, recursively through maps and arrays.
- Support credential helpers (git-credential style): the helper is named by `MYCLI_CREDENTIAL_HELPER`, receives `host=` and `protocol=` on stdin, and answers a `password=` line.
- Document secure credential injection patterns.
