# Clean room and contamination

> Read when: you choose between clean and in-situ, or a run looks contaminated by the machine's own skills, plugins, hooks or settings.

A worker that can see your 100 other skills, your hooks and your permission mode is not testing the target. `agentic-maker run` launches the worker with the recipe verified on Claude Code 2.1.302 on a subscription login:

```
claude -p "<prompt>" --restricted --strict-mcp-config --plugin-dir <target> --add-dir <target> \
  --tools "<list>" --allowedTools <list> --permission-mode dontAsk \
  --output-format stream-json --verbose --include-hook-events --session-id <uuid> \
  --max-turns N --max-budget-usd B --model sonnet
```

What each part does, observed:

| Part | Effect |
|---|---|
| `--restricted` | ignores user, project and local settings and hooks; drops the user's skills, plugins and MCP servers; permission mode `default`; confines the file tools to the working directory and `--add-dir` directories |
| `--strict-mcp-config` | only MCP servers from `--mcp-config` (none, for a skill) |
| `--plugin-dir <target>` | loads the target; skills appear as `<plugin>:<skill>`; a loose skill directory is wrapped in a generated plugin |
| `--add-dir <target>` | lets the worker read the target's own `references/` and `scripts/`. Without it the file tools refuse (`--restricted confines the file tools to the working directory`), the worker cannot follow its skill, and the finding would be harness-induced drift (O6), not a skill defect |
| `--tools` / `--allowedTools` | what exists and what runs without a prompt; anything else is denied, recorded as a `permission_denied` event and in the result |
| `--session-id` | fixed so the record can be found |

## What does not work as a clean room (tested)

- `--bare`: never reads the login, so it needs an API key, and it sends no skill listing (no trigger testing).
- `--safe-mode`: removes skills, hooks and MCP, but also the skills of a `--plugin-dir` target.
- A temporary `CLAUDE_CONFIG_DIR`: the login is lost; the run fails with an API error and zero tokens.
- A plain child `claude -p`: inherits everything (103 skills, 8 plugins, the user's hooks, `bypassPermissions`).

## The contamination report

Every take writes `env.json` from the worker's `init` event: model, version, permission mode, tools, skills, plugins, MCP servers, hook events, and `isolated: true|false` (`false` if any plugin other than the target and the built-in ones loaded, or any hook ran). A run that is not isolated says so; never claim isolation you did not get. `run` also drops `HERDR_*` and `ANTHROPIC_MODEL` from the worker's environment and passes only an allowlist of variables.

## In-situ

`isolation: in-situ` (opt-in) tests collisions: the target's description competing with the skills a real user has installed. That is a real failure class (T2). Use clean rounds to fix text and one in-situ round to confirm. `existing` records have whatever isolation they had; read `env.json`.

## Limits

`--restricted` confines the file tools, not `Bash`. A target that can do damage through shell commands needs throwaway fixtures and a temp workspace (the default), and `allowed_tools` should list only the `Bash(...)` patterns the task needs.
