# Non-Interactive Behaviour

> Read when: a command may prompt, and an agent running without a terminal must never hang or guess.

<!-- src: audit-agentic-cli/references/execution-patterns.md#4. Non-Interactive Mode | audit-agentic-cli/references/execution-patterns.md#Essential Flags -->
## Essential flags

| Flag | Behavior |
|------|----------|
| `--non-interactive` / `--no-input` | Fail immediately if prompt needed |
| `--yes` / `-y` | Auto-confirm prompts (still validates) |
| `--force` / `-f` | Bypass safety checks (explicit risk) |

> Reconciled: the sources had a confirm helper that returned an error in one language, returned false (then exited 1) in two others. This file uses one rule. Without a TTY and without `--yes`/`--force`, a confirming command fails with exit 2 (`usage`) and the message names the flag to add (`--yes` or `--force`). It never returns false silently and never hangs. In `--json` mode the failure is the usual error envelope on stdout with `class: usage`.

```bash
$ mycli delete resource res_001 --json < /dev/null
{"ok":false,"error":{"class":"usage","code":"CONFIRMATION_REQUIRED","message":"Confirmation required in non-interactive mode.","retryable":false,"suggestion":"Re-run with --yes to confirm, or --dry-run to preview."}}
$ echo $?
2
```

Rules:

- A prompt for free-text input in non-interactive mode fails the same way (exit 2, naming the flag or argument that supplies the value).
- Prompts, spinners and banners go to stderr, never stdout.
- `--yes` auto-confirms but still validates input; `--force` additionally bypasses safety checks.
- Pair destructive commands with `--dry-run` (`dry-run.md`).

> Reconciled: the Python source printed "Aborted" and exited 1 when a human answered "no", but 1 means `crash`. A declined confirmation exits 2, the same code as a confirmation that cannot be asked: in both cases the confirmation was not given and nothing was changed. Print `Aborted: confirmation not given` on stderr.

<!-- src: audit-agentic-cli/references/execution-patterns.md#TTY Detection -->
## TTY detection

A CLI is interactive only if all of these hold:

1. The mode is not forced non-interactive by `--non-interactive` / `--no-input` or by the environment variable (see below).
2. stdin is a TTY.
3. stdout is a TTY.

Three modes exist: auto (detect, the default), interactive (forced), non-interactive (forced). Anything else is non-interactive.

Implementations (prompt and confirm helpers): `../frameworks/go/execution-patterns-safety.md`, `../frameworks/python/execution-patterns-safety.md`, `../frameworks/node/execution-patterns-safety.md`.

<!-- src: audit-agentic-cli/references/execution-patterns.md#Environment Variable Support -->
## Environment variable support

Set globally for CI/CD; every command then runs non-interactively.

```bash
export MYCLI_NON_INTERACTIVE=1
export MYCLI_AUTO_YES=1

mycli deploy
mycli delete resource
```
