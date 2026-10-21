# Target: a CLI or script

> Read when: the target is an executable an agent will drive through a shell.

**Exposure:** the binary is put on the worker's `PATH` under `bin_name` and the matching `Bash(<name> *)` patterns are allowed; the worker gets only `--help` (cold). Give the scenario a built binary: a crate or package name is not a path (`bin:`, and `build:` to say how it is produced).

**Lens:**
1. **Discovery from help:** did it find the right subcommand and flag from `--help` alone?
2. **Streams and exit codes (O7):** did it parse stdout, did stderr pollute it, did it read an exit code as success or failure correctly?
3. **Non-interactive behaviour:** a prompt or pager that hangs; a missing `--yes`; no TTY.
4. **Recovery (C5):** after an error, did the message tell it what to change, or did it retry the same command?
5. **Ambiguity (M7):** two subcommands that look alike.
6. **Safety:** did it reach for a destructive command without a dry-run? The scenario's `allowed_tools` should list only what the task needs.

**Typical scenarios:** the first task a new user does; a task whose first attempt fails (wrong id, missing auth) to see what the error teaches; a task at scale (many items, pagination).

The audit side of the same target is `/agentic-maker:audit`; derailment shows what an agent actually does with the contract the audit checks.
