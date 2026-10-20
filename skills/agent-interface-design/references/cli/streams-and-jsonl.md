# Streams, Verbosity and JSONL

> Read when: you are deciding what goes on stdout versus stderr, or designing a streaming (`--stream`, `--follow`) command.

<!-- src: audit-agentic-cli/references/output-contracts.md#8. Stream Separation Best Practices | audit-agentic-cli/references/output-contracts.md#The Rule -->
## The rule

Proper stream separation is critical for agent consumption.

| Stream | Content |
|--------|---------|
| **stdout** | Machine-parseable results ONLY |
| **stderr** | Progress, warnings, debug info, prompts, spinners |

Never print a banner like `Creating resource...` to stdout ahead of the JSON: the agent cannot parse the mix. Send human text to stderr and the JSON to stdout:

```bash
mycli create resource --name foo --json 2>progress.log   # stdout = one JSON document; progress.log = human text
```

Code showing the bad and good form in each language: `../frameworks/go/output-contracts-streams.md`. When a command must emit a non-JSON artifact (patch, diff, query, prompt, translation), stdout stays one canonical artifact format and status goes to stderr or a sidecar (see `checks.md`).

<!-- src: audit-agentic-cli/references/output-contracts.md#Verbose Mode -->
## Verbose mode

Use `--verbose` / `-v` to increase stderr detail, never stdout.

- `-v` is verbosity level 1 (info)
- `-vv` is level 2 (debug)
- `-vvv` is level 3 (trace)

<!-- src: audit-agentic-cli/references/output-contracts.md#4. JSONL Streaming -->
## JSONL streaming

For long-running operations, use JSON Lines (newline-delimited JSON). Each line is one typed event; see `jsonl-progress-patterns.md` for sequences and `jsonl-event-schema.md` for the schema.

> Reconciled: the sources put JSONL progress events on stdout in one file and on stderr in another. This file uses one rule. A command that streams results emits typed JSONL on stdout, and its last line is `type: summary` or `type: result`. Progress that is not a result (`progress`, `phase`, `heartbeat`, `log` events) goes to stderr, also one JSON object per line. Never mix the two on one stream. The source name `completed` for the terminal event is the same role as `result`; a CLI that already emits `completed` keeps working but documents it.

<!-- src: audit-agentic-cli/references/output-contracts.md#Event Types -->
## Event types

| Type | Description | Required Fields | Stream |
|------|-------------|-----------------|--------|
| `started` | The operation was accepted and is running | `type`, `operation_id` | stderr |
| `progress` | Incremental progress update | `type`, `phase` | stderr |
| `log` | Log message | `type`, `level`, `message` | stderr |
| `completed` | Operation finished (terminal; also called `result` or `summary`) | `type`, `status`, `result` | stdout, last line |
| `error` | Operation failed | `type`, `error` | stdout, last line, with the matching exit code |
| `heartbeat` | Keep-alive signal for long operations | `type` | stderr |
| `phase` | Phase transition marker | `type`, `phase`, `status` | stderr |

Items that are the command's actual results (log lines of `logs --follow`, rows of a streamed list) are result events and go to stdout.

<!-- src: audit-agentic-cli/references/output-contracts.md#Streaming Requirements -->
## Streaming requirements

1. **Include `type` field**: enables event discrimination.
2. **UTC ISO 8601 timestamps**, e.g. `2024-01-15T10:30:00Z`.
3. **Flush after each line**: unbuffered output for real-time processing.
4. **One JSON object per line**: no pretty-printing in stream mode.
5. **Heartbeats for long operations**: emit every 30s to prevent timeout detection.
6. **Monotonic progress**: percent never decreases within a phase.

<!-- src: audit-agentic-cli/references/output-contracts.md#Quick Reference | audit-agentic-cli/references/output-contracts.md#Output Mode Flags -->
## Output mode flags

| Flag | Output Type | Use Case |
|------|-------------|----------|
| (none) | Human-readable | Interactive terminal use |
| `--json` | JSON envelope | Agent/script consumption |
| `--quiet` | Bare IDs/values | Pipelines, variable capture |
| `--verbose` | Detailed stderr | Debugging |
| `--stream` / `--follow` | JSONL events | Real-time progress monitoring |
