# inventory (spec)

A small command-line tool that an AI agent will drive in a shell. It lists and trims an item inventory.

Built-in items: `1 widget`, `2 gadget`, `3 gizmo`. After the first change the state is kept in `./inventory.json`.

## Commands
- `inventory list [--json]` shows all items.
- `inventory get <id> [--json]` shows one item.
- `inventory remove <id> [--yes | --dry-run] [--json]` deletes an item for good. It must never prompt: without `--yes` or `--dry-run` it refuses.
- `inventory --version`, `inventory -h | --help`.

## Contract
- Data on stdout, diagnostics on stderr. With `--json`, stdout is exactly one JSON object: `{"ok": true, "result": ...}` or `{"ok": false, "error": {"class", "code", "message", "retryable", "suggestion"}}`. Errors are JSON too.
- Exit codes: 0 success, 2 usage error (unknown command or option, missing id, `remove` without `--yes` or `--dry-run`), 3 item not found.
- Help text shows examples and lists the exit codes.
- One file, Python 3 standard library only.
