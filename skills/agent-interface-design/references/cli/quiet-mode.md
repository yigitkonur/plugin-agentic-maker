# Quiet Mode

> Read when: an agent or script pipes one CLI into another, or captures an ID in a variable.

<!-- src: audit-agentic-cli/references/output-contracts.md#7. Quiet Mode -->
## What `--quiet` prints

`--quiet` or `-q` produces minimal, pipeline-friendly output: bare values, no envelope.

```bash
# List: Just IDs, one per line
$ mycli list resources --quiet
res_001
res_002
res_003

# Create: Just the new ID
$ mycli create resource --name foo --quiet
res_004

# Delete: No output on success
$ mycli delete resource res_001 --quiet
```

If `--quiet` and `--json` are both given, the CLI must pick one deterministically and document which (the Go reference prints the bare ID when `--quiet` is set, before checking `--json`). Errors still use the exit codes in `exit-codes.md`.

<!-- src: audit-agentic-cli/references/output-contracts.md#When to Use Quiet Mode -->
## When to use quiet mode

- Piping to other commands: `mycli list --quiet | xargs -n1 mycli get`
- Capturing IDs in variables: `ID=$(mycli create --quiet)`
- Counting results: `mycli list --quiet | wc -l`

A Go implementation is in `../frameworks/go/output-contracts.md`.
