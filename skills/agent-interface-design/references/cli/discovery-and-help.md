# Discovery and Help

> Read when: you are designing or auditing how a CLI exposes its flags, command grammar, help text, version and capabilities to an agent.

Go/Cobra code for everything here is in `../frameworks/go/discovery-and-auth.md`. Exit codes live in `exit-codes.md`; envelopes in `envelope-and-errors.md`.

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#Standard Flag Reference | audit-agentic-cli/references/discovery-and-auth.md#Standard Flags (All Commands) -->
## Standard flags

A well-designed CLI supports these flags consistently on every command.

| Flag | Short | Type | Purpose | Example |
|------|-------|------|---------|---------|
| `--json` | `-j` | bool | Structured JSON output for machine parsing | `mycli list --json` |
| `--quiet` | `-q` | bool | Suppress non-essential output (warnings, info) | `mycli deploy -q` |
| `--verbose` | `-v` | bool | Increase verbosity (debug info, timing) | `mycli run -v` |
| `--yes` | `-y` | bool | Skip all confirmations / auto-approve | `mycli delete all -y` |
| `--dry-run` | | bool | Preview changes without executing | `mycli apply --dry-run` |
| `--force` | `-f` | bool | Override safety checks and guards | `mycli rm protected -f` |
| `--output` | `-o` | string | Output format: `json`, `yaml`, `table`, `text` | `mycli get -o yaml` |
| `--timeout` | | duration | Operation timeout (e.g., `30s`, `5m`) | `mycli sync --timeout 2m` |
| `--no-input` | | bool | Non-interactive mode; fail if input needed | `mycli setup --no-input` |
| `--help` | `-h` | bool | Show help for command | `mycli deploy -h` |

> Unresolved: the sources disagree on three details. (1) `--json` has short form `-j` in one file and none in the others. (2) `--timeout` has no short form in one file and `-t` (seconds) in another; the examples use a duration string, the agent guide a number of seconds. (3) The non-interactive switch is `--no-input` in one file and `--non-interactive` in the code examples. Pick one spelling per CLI, document it in `--help`, and keep it identical across commands.

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#Flag Behavior Matrix -->
## Flag behavior matrix

| Environment | `--json` | `--quiet` | `--verbose` | Colors | Prompts |
|-------------|----------|-----------|-------------|--------|---------|
| TTY (human) | Off | Off | Off | On | On |
| CI | Auto-on | Auto-on | Off | Off | Off |
| Piped | Auto-on | Auto-on | Off | Off | Off |
| `--no-input` | Unchanged | Unchanged | Unchanged | Unchanged | Off |

> Reconciled: the sources gave exit 2, a generic error, and `false`/exit 1 for a confirming command run with no TTY. This file uses: without a TTY and without `--yes`/`--force`, a confirming command fails with exit 2 naming the flag. It never returns false silently and never hangs. Environment detection is in `config-and-env.md`.

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#1. Command Grammar | audit-agentic-cli/references/discovery-and-auth.md#Noun-Verb Hierarchy (Preferred) -->
## Command grammar

Prefer a noun-verb hierarchy:

```
mycli <noun> <verb> [args] [flags]

mycli user create --name alice
mycli user list --json
mycli user delete alice

mycli deployment apply -f deploy.yaml
mycli deployment status my-app
```

Benefits: hierarchical discovery (`mycli --help` then `mycli user --help`), related actions grouped, predictable exploration.

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#Consistent Flag Naming -->
## Consistent flag naming

- Short flags: reserve single letters for frequently used flags (`-j`, `-q`, `-v`, `-y`, `-f`, `-o`, `-h`).
- Boolean defaults: every boolean flag defaults to `false`.
- Negation: support `--no-<flag>` to disable a default (for example `--no-wait`).
- Profiles: use `--profile` / `-p` to select a config profile (see `config-and-env.md`).

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#2. Self-Documenting Help | audit-agentic-cli/references/discovery-and-auth.md#Help Should Answer 5 Questions -->
## Help answers five questions

1. What does this command do?
2. What arguments are required?
3. What flags are available?
4. What output formats exist?
5. What are realistic examples?

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#Good Help Example -->
## Good help example

```
Deploy a service to the target environment.

Usage:
  mycli deploy <service-name> --env <environment> [flags]

Arguments:
  service-name    Name of the service to deploy (required)

Flags:
      --env string        Target environment: dev, staging, prod (required)
      --image string      Container image override (default: from config)
      --replicas int      Number of replicas (default: from config)
      --dry-run           Preview changes without applying
      --wait              Wait for deployment to complete (default: true)
      --timeout duration  Maximum wait time (default: 5m)
      --json              Output result as JSON

Examples:
  # Deploy to staging
  mycli deploy web-api --env staging

  # Deploy specific image to production
  mycli deploy web-api --env prod --image myregistry/web:v2.1.0 --json

  # Preview deployment changes
  mycli deploy web-api --env dev --dry-run
```

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#Machine-Readable Help (Emerging Pattern) -->
## Machine-readable help

An emerging pattern: `mycli help --json` returns the structured command tree with parameter schemas, so an agent does not have to scrape help text. A Node/Commander sketch is in `../frameworks/node/examples.md`.

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#3. Version and Capabilities -->
## Version and capabilities

`mycli version --json` reports the version and what the CLI can do, so an agent can branch on `capabilities` instead of guessing:

```json
{
  "version": "2.1.0",
  "git_commit": "abc123",
  "build_date": "2024-01-15",
  "go_version": "1.21",
  "capabilities": ["streaming", "batch", "dry-run-server"],
  "api_version": "v2"
}
```

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#Common Commands -->
## Common discovery commands

| Pattern | Command | Purpose |
|---------|---------|---------|
| Help | `mycli <cmd> --help` | Discover flags and examples |
| Version | `mycli version --json` | Get capabilities |
| Auth status | `mycli auth status --json` | Check credentials |
| Config debug | `mycli config show --effective` | See config sources |
| Env check | `mycli env --json` | Detect runtime context |
| Secure auth | `echo $TOKEN \| mycli auth login --token-stdin` | No process exposure |
