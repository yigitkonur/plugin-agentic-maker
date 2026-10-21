# Conventions Shared by the Code Examples

> Read when: you are porting a CLI pattern between Go, Python, Node, Rust and Bash, or checking that two implementations agree on flags, exit codes and envelope.

The per-language code is under `../frameworks/<stack>/`. The envelope fields are in `envelope-and-errors.md`; the exit codes in `exit-codes.md`; the error classes in `error-classes.md`.

<!-- src: audit-agentic-cli/references/examples.md#Standard Flag Names -->
## Standard flag names

Every example uses the same flag names:

| Flag | Short | Purpose |
|------|-------|---------|
| `--json` | | Output as JSON (not `--output json`) |
| `--quiet` | `-q` | Minimal output |
| `--yes` | `-y` | Auto-confirm prompts |
| `--dry-run` | | Preview without executing |
| `--force` | `-f` | Force operation |
| `--timeout` | | Operation timeout |

The full flag set, including `--output`, `--no-input` and `--verbose`, is in `discovery-and-help.md`.

<!-- src: audit-agentic-cli/references/examples.md#Cross-Language Consistency Reference | audit-agentic-cli/references/examples.md#Standard Flags | audit-agentic-cli/references/examples.md#Exit Codes -->
## Cross-language consistency

All examples follow the same standards. Each of these flags is implemented in Go, Python, Node, Rust and Bash:

| Flag | Short |
|------|-------|
| `--json` | - |
| `--quiet` | `-q` |
| `--yes` | `-y` |
| `--dry-run` | - |
| `--force` | `-f` |
| `--timeout` | - |

Each exit code `0` success, `1` crash, `2` usage, `3` not_found, `4` auth, `5` conflict, `6` validation, `7` transient and `8` partial is implemented in all five stacks, and the same JSON envelope is produced by all of them.

> Note: the code in `frameworks/` uses the 0-8 exit table, `ExitAuth`/`Auth`, the class `network` for the exit-7 example (`transient` is the exit-7 group, not a class), and writes the envelope for success and failure to stdout; the tests read stdout only. Lists use `result.items` and `result.total`.

<!-- src: audit-agentic-cli/references/examples.md#Standard JSON Envelope | audit-agentic-cli/references/examples.md#JSON Envelope -->
## Envelope used by the examples

Every example emits the envelope `ok`, `command`, `result`, `error` (`class`, `code`, `message`, `retryable`, `suggestion`) and `meta` (`truncated`, `total_count`, `duration_ms`), defined in `envelope-and-errors.md`. Success sets `error: null`; failure sets `result: null` and, for example, `"class": "not_found"`, `"code": "RESOURCE_NOT_FOUND"`, `"suggestion": "Try 'mycli resource list' first"`.

> Note: the class list is in `error-classes.md` (`usage, not_found, auth, conflict, validation, rate_limit, timeout, network, dependency_failed, internal, partial_success`).
