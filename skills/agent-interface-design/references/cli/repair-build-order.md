# Repair Build Order, Minimum Envelope and Repair Loop

> Read when: you are fixing an existing CLI step by step, or designing a command whose output the agent must repair and resubmit.

<!-- src: audit-agentic-cli/SKILL.md#Minimum Output Envelope -->
## Minimum output envelope

Aim for one stable JSON envelope across all commands.

Success:

```json
{ "ok": true, "result": {}, "error": null, "schema_version": "v1" }
```

Failure:

```json
{
  "ok": false,
  "result": null,
  "error": {
    "class": "validation",
    "code": "MISSING_FLAG",
    "message": "Flag --target is required.",
    "retryable": false,
    "suggestion": "Run `mycli deploy --target <name>`."
  },
  "schema_version": "v1"
}
```

Stdout = data channel. Stderr = operator channel. Exit code = semantic class. All three must agree. In `--json` mode the failure envelope above is written to stdout, with exit 6 here (`validation`).

The fuller envelope with `command` and `meta` is in `envelope-and-errors.md`; the `schema_version` spelling (`"v1"` here, `"1.0"` there) is recorded as unresolved in `envelope-schemas.md`.

<!-- src: audit-agentic-cli/SKILL.md#Build Order (Repair Existing CLI) -->
## Build order

When fixing an existing CLI, do the work in this order. Skipping ahead wastes effort.

1. Pure JSON output and stdout/stderr separation (`streams-and-jsonl.md`).
2. Structured errors and semantic exit codes (`error-classes.md`, `exit-codes.md`).
3. Non-interactive flags and safe defaults: `--no-input`, `--yes`, `--dry-run` (`non-interactive.md`, `dry-run.md`).
4. Iterative feedback loops for any command whose output the agent might need to repair (below).
5. Discovery: help text, examples, documented exit codes and output fields (`discovery-and-help.md`).
6. Async / JSONL / job-style flows for long-running operations (`async-and-long-running.md`).

<!-- src: audit-agentic-cli/SKILL.md#Iterative Repair Loop -->
## Iterative repair loop

Use this pattern when an agent generates an artifact, the CLI validates it, and the agent must repair on rejection.

```
input artifact -> CLI validation -> structured diff/errors -> agent repair -> retry -> accepted -> finalize
```

Typical fits: translation/localization batches, code generation with validation gates, manifest/config/migration generation, bulk import or sync.

Each iteration must tell the agent:

- current stage
- accepted / rejected / partial
- what failed, with identifiers or locations
- whether the failure is retryable
- the next command to run (`next_action.command`)
- progress complete vs work remaining

One-shot read/list/get/status commands do not need this; use the simpler envelope. The steering text carried in `next_action` is a lever and an injection surface: see `../decisions/steering-contract.md`. Retry budget, phases and finalization criteria are part of the design deliverable (`skills/design/references/cli-deliverables.md`).
