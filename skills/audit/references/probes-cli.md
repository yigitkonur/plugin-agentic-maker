# The CLI probes

> Read when: you run, or have to explain, `agentic-maker probe cli` or `probe cli-diff`, including what replaced the old help-scan and help-diff scripts. MCP probes: [probes-mcp](probes-mcp.md).

The probes observe a surface the way an agent meets it. They replace helper scripts that only scanned text.

<!-- src: audit-agentic-cli/scripts/audit-cli-help.md#audit-cli-help.sh -->
## `probe cli` (replaces `audit-cli-help.sh`)

The old script was a read-only discoverability scan. `probe cli` keeps that scan (standard flags, examples, exit codes) and adds what the script said it could not do - separation of stdout and stderr, real JSON parsing and failure paths - by running the commands you declare safe.

<!-- src: audit-agentic-cli/scripts/audit-cli-help.md#Inputs -->
### Inputs
`agentic-maker probe cli <CLI>` where `<CLI>` is a path or a command name. `--sub "repo view"` (repeatable) or `--subcommands FILE` lists subcommands whose `--help` is checked (blank lines and `#` comments in the file are ignored). `--safe "<args>"` (repeatable) or `--safe-cmds FILE` lists read-only commands the probe may run, with an optional `# expect-exit N`.

<!-- src: audit-agentic-cli/scripts/audit-cli-help.md#Commands Run -->
### Commands run
Only: `CLI --help`, `CLI --version`, `CLI <subcommand> --help` for each listed subcommand, one invalid command (`__agentic_maker_probe_no_such_command__`), and the commands declared safe. Never list, get, create, update, delete, deploy or login unless you declared it. Every run is in an empty temp directory, with a minimal environment, stdin closed, a timeout and its own process group. A script that does not mention `--help` or read its arguments is not run at all: `--help` on it would just run it (the result says so under `not_executed`).

<!-- src: audit-agentic-cli/scripts/audit-cli-help.md#Output -->
### Output
One envelope (`--human` prints a short report): `executed` (exact commands and exit codes), `not_executed`, `findings` (check, severity, why it matters to an agent, fix, evidence, the reference to read), per-subcommand help status with examples and exit codes, standard flag coverage (`--json --output --quiet --yes --dry-run --force --no-input --timeout`), and the probe's own limits. Exit 0 with no findings, 8 when there are findings.

<!-- src: audit-agentic-cli/scripts/audit-cli-help.md#Example -->
### Example
```
agentic-maker probe cli gh --sub "repo view" --sub "issue list" --safe "repo view cli/cli --json name"
agentic-maker probe cli ./target/debug/mycli --safe-cmds safe.txt --human
```

<!-- src: audit-agentic-cli/scripts/audit-cli-help.md#Limitations -->
### Limitations
A black-box probe of read-only commands: it does not prove a CLI is agent-ready. Flag detection is text-based and can miss unusual help formats. Commands not declared safe were not run, so destructive flows are judged from the help text only. Subcommand lines are split with shell quoting rules.

<!-- src: audit-agentic-cli/scripts/diff-cli-help.md#diff-cli-help.sh -->
## `probe cli-diff` (replaces `diff-cli-help.sh`)
Compares two saved help snapshots without running the CLI.

<!-- src: audit-agentic-cli/scripts/diff-cli-help.md#Inputs -->
### Inputs
`agentic-maker probe cli-diff OLD NEW`: two plain text files. Capture them with a separate read-only call (`mycli --help > old.txt`); for a large CLI concatenate top-level and subcommand help into each snapshot.

<!-- src: audit-agentic-cli/scripts/diff-cli-help.md#Output -->
### Output
Added and removed commands, added and removed flags, and likely breaking changes: a removed command, a removed flag, or a changed `Usage:` line. Exit 8 when something looks breaking.

<!-- src: audit-agentic-cli/scripts/diff-cli-help.md#Safe Usage -->
### Safe usage
Reads files only; the CLI under audit is never executed.

<!-- src: audit-agentic-cli/scripts/diff-cli-help.md#Example -->
### Example
`agentic-maker probe cli-diff snapshots/v1-help.txt snapshots/v2-help.txt`

<!-- src: audit-agentic-cli/scripts/diff-cli-help.md#Limitations -->
### Limitations
Command extraction is heuristic and works best with conventional `Commands:` or `Subcommands:` sections. Aliases, hidden commands and per-command flag scopes are invisible unless they appear in the snapshot. It cannot prove runtime compatibility; pair it with real stdout/stderr and exit-code checks before calling a CLI agent-ready.
