# Transaction and Rollback

> Read when: a command runs several dependent steps and a mid-way failure must not leave half-applied state.

<!-- src: audit-agentic-cli/references/execution-patterns.md#6. Transaction/Rollback | audit-agentic-cli/references/execution-patterns.md#Multi-Step Operations -->
## Multi-step operations

```bash
# Automatic rollback on failure
mycli deploy --rollback-on-failure

# Manual checkpoint-based rollback
mycli rollback --to checkpoint_abc123
```

Pattern:

- Model the operation as ordered steps; each has an `Execute` and an optional `Undo`.
- Record which steps completed. On failure with `--rollback-on-failure`, run the `Undo` of completed steps in reverse order.
- If an `Undo` itself fails, log it and continue rolling back the rest; do not abort the rollback.
- Fail with an error naming the failed step (`step <name> failed`).
- Report in the response which steps were rolled back and which checkpoints were preserved (see the cancellation response in `timeouts-and-signals.md`).

Example step order for a deploy: `create-database`, `run-migrations`, `deploy-application`, each with its own undo (`deleteDatabase`, `rollbackMigrations`, `rollbackApp`).

Go implementation: `../frameworks/go/execution-patterns-safety.md`.
