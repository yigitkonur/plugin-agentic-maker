---
name: agent-interface-design
description: Guidance for building or reviewing anything an AI agent calls or reads - a CLI or script (JSON output, exit codes, --help, error messages), an MCP server or tool (descriptions, schemas, responses), or a skill. Use for "make it agent-friendly", "my agent keeps failing to parse / picks the wrong tool", tool descriptions, error messages. Not for human-facing UI.
---

# Agent-interface design

An agent is the user of this surface: it reads the text, picks the call, parses the answer and decides what to do next. Paths below are relative to `${CLAUDE_SKILL_DIR}/references/`.

## The eight questions

Answer them for the surface in front of you, cold. Detail and the CLI / MCP / skill version of each: [contract.md](references/contract.md).

1. **Intent** - built around the agent's task, not around endpoints? 2. **Contract** - inputs, outputs, errors machine-checkable? 3. **Discovery** - learnable from the surface itself, with examples? 4. **Steering** - does each answer say what to do next? 5. **Safety** - destructive steps explicit, secrets off the command line? 6. **Budget** - proportionate cost in context? 7. **Recovery** - do errors teach? 8. **Verification** - can it be exercised non-interactively without hanging?

## Rules that settle most arguments

- stdout is data, stderr is the operator, the exit code is the class, and all three agree. Errors in `--json` mode are JSON too.
- A description is a prompt. Start with Verb + Resource, say when to use it, keep it under about 100 tokens.
- An error that names the field, the expected value and the next call is worth more than any retry logic.
- Fix the surface before blaming the architecture: most "MCP is wrong" or "the model is weak" turns out to be an unparseable stdout or an error that teaches nothing.
- Facts that age (versions, client matrices, prices, model behaviour) live in `fresh/` with a date. Re-check before citing; never present them as current.

## Where to read

| Situation | Read |
|---|---|
| Choosing CLI, MCP or a skill | [decisions/surface-choice.md](references/decisions/surface-choice.md) |
| Designing or fixing a CLI | [cli/checks.md](references/cli/checks.md) (five checks, severity, finish criteria), [cli/repair-build-order.md](references/cli/repair-build-order.md), then [index-cli.md](references/index-cli.md) |
| Output, errors, exit codes | [cli/envelope-and-errors.md](references/cli/envelope-and-errors.md), [cli/exit-codes.md](references/cli/exit-codes.md), [cli/streams-and-jsonl.md](references/cli/streams-and-jsonl.md) |
| A prompt, a hang, a destructive command | [cli/non-interactive.md](references/cli/non-interactive.md), [cli/dry-run.md](references/cli/dry-run.md) |
| Designing or fixing an MCP server | [mcp/hard-rules.md](references/mcp/hard-rules.md) (the 15 rules), [mcp/quick-reference.md](references/mcp/quick-reference.md), then [index-mcp-1.md](references/index-mcp-1.md) |
| Tool descriptions, schemas, responses | [mcp/descriptions-structure-and-length.md](references/mcp/descriptions-structure-and-length.md), [mcp/schemas-flat-and-sized.md](references/mcp/schemas-flat-and-sized.md), [mcp/responses-curated-and-semantic.md](references/mcp/responses-curated-and-semantic.md) |
| Steering an agent through tool output | [decisions/steering-contract.md](references/decisions/steering-contract.md) |
| Security and auth | [decisions/security-posture.md](references/decisions/security-posture.md), then the `mcp/security/` pages in [index-mcp-2.md](references/index-mcp-2.md) |
| Code for a language or SDK | the `frameworks/<stack>/` pages in [index-frameworks-1.md](references/index-frameworks-1.md) (Go, Python, Node, Rust, Bash, MCP SDKs) |
| Anything dated: clients, models, platforms, registries | [index-fresh-1.md](references/index-fresh-1.md); open the file and read its `as_of` first |
| Not sure which file | the indexes: [cli](references/index-cli.md), [decisions](references/index-decisions.md), mcp ([1](references/index-mcp-1.md), [2](references/index-mcp-2.md), [3](references/index-mcp-3.md)), frameworks ([1](references/index-frameworks-1.md), [2](references/index-frameworks-2.md), [3](references/index-frameworks-3.md)), fresh ([1](references/index-fresh-1.md), [2](references/index-fresh-2.md), [3](references/index-fresh-3.md)) |

## Evidence instead of opinion

- `/agentic-maker:audit <target>` probes a CLI, script, MCP server or skill and reports against the contract. It changes nothing.
- `/agentic-maker:derail <target>` runs fresh agents on realistic tasks, reads what they did and rewrites the text that misled them.
- `/agentic-maker:design <idea>` interviews you, then sketches the surface before any code.
