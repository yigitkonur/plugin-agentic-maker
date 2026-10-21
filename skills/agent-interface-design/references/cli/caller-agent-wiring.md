# Wiring a CLI into an Agent

> Read when: you are giving an agent instructions or a tool definition for running a CLI, and need the flags it should always pass.

Wrapper logic is in `caller-integration.md`; resilience in `caller-resilience.md`. Provider-specific tool definitions (Anthropic, OpenAI, LangChain, AutoGen) are in `../frameworks/node/agent-integration-frameworks.md` and `../frameworks/python/agent-integration.md`.

<!-- src: audit-agentic-cli/references/agent-integration.md#6. Agent System Prompt Template -->
## System prompt template

Paste this into the agent's instructions:

````markdown
## CLI Usage Guidelines

When using CLI tools, follow these patterns:

1. **Always use --json flag** for structured output
2. **Check exit codes** before parsing output:
   - 0 = success, parse result
   - 3 = not found, resource missing
   - 4 = auth error, re-authenticate
   - 7 = transient, retry with backoff
3. **Read error.suggestion** field for recovery hints
4. **Use --yes flag** to skip confirmations
5. **Handle timeouts** - set reasonable limits

Example invocation:
```bash
mycli resource get RESOURCE_ID --json --yes
```

Parse response:
```json
{"ok": true, "result": {"id": "...", "status": "active"}}
```
````

<!-- src: audit-agentic-cli/references/agent-integration.md#7. Provider Tool Schema Example -->
## Generic tool schema

A single tool that runs the CLI (the parameter descriptions carry the examples):

```json
{
  "name": "invoke_cli",
  "description": "Execute CLI command and return structured result",
  "parameters": {
    "type": "object",
    "properties": {
      "command": {
        "type": "string",
        "description": "Base CLI command (e.g., 'mycli resource create')"
      },
      "args": {
        "type": "object",
        "description": "Named arguments as key-value pairs"
      },
      "flags": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Boolean flags (e.g., ['--json', '--yes'])"
      }
    },
    "required": ["command"]
  }
}
```

<!-- src: audit-agentic-cli/references/agent-integration.md#15. Standard CLI Flags Reference -->
## Flags an agent passes

| Flag | Short | Description | When to Use |
|------|-------|-------------|-------------|
| `--json` | `-j` | Structured JSON output | **Always** in agent context |
| `--quiet` | `-q` | Suppress non-essential output | Cleaner parsing, reduce noise |
| `--yes` | `-y` | Auto-approve confirmations | Non-interactive automation |
| `--timeout <duration>` | | Set operation timeout | Long-running tasks, prevent hangs |
| `--dry-run` | | Preview without executing | Validation before commit |
| `--force` | `-f` | Override safety checks | Conflict resolution |
| `--verbose` | `-v` | Extra debug output | Troubleshooting (not for agents) |

The flag set matches `discovery-and-help.md`, where the short-form and spelling disagreements between the sources are listed.

<!-- src: audit-agentic-cli/references/agent-integration.md#Flag Usage Patterns -->
## Flag usage patterns

```bash
# Standard agent invocation
mycli task start prompt.md --json --quiet --yes --timeout 300

# Dry run validation
mycli resource create config.yaml --json --dry-run

# Force overwrite on conflict
mycli resource update id --json --yes --force

# Verbose for debugging (human use)
mycli task start prompt.md --json --verbose 2>&1 | tee debug.log
```

Do not merge stderr into stdout (`2>&1`) when the output feeds a parser; the debugging line above is for a human reading a log.
