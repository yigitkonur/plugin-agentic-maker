---
name: agent-interface-design
description: Use when building, changing or reviewing something an AI agent will call or read: an MCP server or its tools (names, descriptions, schemas, errors, responses), a CLI or script an agent runs (JSON output, exit codes, --help), or a SKILL.md. Also for "make it agent-friendly" and "my agent keeps misparsing or picking the wrong tool". Not for human UI.
---

# Agent-interface design

> In Codex: `$ARGUMENTS` is what the user wrote after the skill name. `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_SKILL_DIR}` mean the plugin folder and this skill's folder (the plugin folder is two levels above this file); `agentic-maker` is on PATH or is `<plugin folder>/bin/agentic-maker`. A line that starts with an exclamation mark and a backtick is a command: run it yourself first.

An agent is the user of this surface: it reads the text, picks the call, parses the answer and decides what to do next. Paths below are relative to `${CLAUDE_SKILL_DIR}/references/`; a path that starts with `skills/` is relative to the plugin root (the folder that holds `skills/`).

## The eight questions

Answer them for the surface in front of you, cold. Detail and the CLI / MCP / skill version of each: [contract.md](references/contract.md).

1. **Intent** - built around the agent's task, not around endpoints? 2. **Contract** - inputs, outputs, errors machine-checkable? 3. **Discovery** - learnable from the surface itself, with examples? 4. **Steering** - does each answer say what to do next? 5. **Safety** - destructive steps explicit, secrets off the command line? 6. **Budget** - proportionate cost in context? 7. **Recovery** - do errors teach? 8. **Verification** - can it be exercised non-interactively without hanging?

## Rules that settle most arguments

- stdout is data, stderr is the operator, the exit code is the class, and all three agree. Errors in `--json` mode are JSON too.
- A description is a prompt. Start with Verb + Resource, say when to use it, keep it under about 100 tokens.
- An error that names the field, the expected value and the next call is worth more than any retry logic.
- Fix the surface before blaming the architecture: most "MCP is wrong" or "the model is weak" turns out to be an unparseable stdout or an error that teaches nothing.
- Facts that age (versions, client matrices, prices, model behaviour) live in `fresh/` with a date. Re-check before citing; never present them as current.

## Check what you built

After you build or change a CLI or an MCP server, run the plugin's probe on it before you say it is done. `agentic-maker` is on your Bash PATH while the plugin is enabled; the probe reads and runs the surface the way an agent would, and changes nothing.

- **CLI or script:** `agentic-maker probe cli <binary> --safe "<read-only args>" --safe "<read-only args>"`. Its reply lists the help text, `suggested_safe` commands and a ready next command. Never put a command that creates, updates, deletes, deploys or sends in `--safe`, not even with a dry-run flag: whether the flag is honoured is what you are checking.
- **MCP server:** `agentic-maker probe mcp "<the command that starts it>"`; add `--call 'tool={}'` only for tools that are read-only.

Every finding names the file under `references/` that holds the rule and the fix. Fix, probe again, and stop when no High finding is left. A skill is checked by a run, which only the user starts: `/agentic-maker:derail <skill>`.

## When an agent already misbehaved

Read what it did instead of guessing: `agentic-maker normalize session:<id>` (Claude Code, Codex or agy; the id is in the harness status line, or `herdr agent get <pane>` has it) writes `trace.md`, one `[n]` line per event. Read it by the dimensions of the `derailment-method` skill and name the sentence, example or message that led the agent there. The user can fix and rerun with `/agentic-maker:derail <target> --runner existing --from session:<id>`.

## Where to read

| Situation | Read |
|---|---|
| Writing a skill or its description | [skill/descriptions-that-trigger.md](references/skill/descriptions-that-trigger.md), [skill/text-as-program.md](references/skill/text-as-program.md); a whole new skill: the user starts `/agentic-maker:build-skill` (frontmatter, layout, checklist, testing) |
| Choosing CLI, MCP or a skill | [decisions/surface-choice.md](references/decisions/surface-choice.md) |
| Designing or fixing a CLI | [cli/checks.md](references/cli/checks.md) (five checks, severity, finish criteria), [cli/repair-build-order.md](references/cli/repair-build-order.md), then [index-cli.md](references/index-cli.md) |
| Output, errors, exit codes | [cli/envelope-and-errors.md](references/cli/envelope-and-errors.md), [cli/exit-codes.md](references/cli/exit-codes.md), [cli/streams-and-jsonl.md](references/cli/streams-and-jsonl.md) |
| A prompt, a hang, a destructive command | [cli/non-interactive.md](references/cli/non-interactive.md), [cli/dry-run.md](references/cli/dry-run.md) |
| Designing or fixing an MCP server | [mcp/hard-rules.md](references/mcp/hard-rules.md) (the 15 rules), [mcp/quick-reference.md](references/mcp/quick-reference.md) |
| Tool descriptions, schemas, responses | [mcp/descriptions-structure-and-length.md](references/mcp/descriptions-structure-and-length.md), [mcp/schemas-flat-and-sized.md](references/mcp/schemas-flat-and-sized.md), [mcp/responses-curated-and-semantic.md](references/mcp/responses-curated-and-semantic.md) |
| A tool that deletes, sends or pays | [mcp/security/least-privilege-and-confirmation.md](references/mcp/security/least-privilege-and-confirmation.md): annotations, confirmation, what a client may trust |
| Steering an agent through tool output | [decisions/steering-contract.md](references/decisions/steering-contract.md) |
| Security and auth | [decisions/security-posture.md](references/decisions/security-posture.md), then the `mcp/security/` pages |
| Anything dated: clients, models, platforms, registries | the `fresh/` pages; open the file and read its `as_of` first |

Code for a stack (generated from the folders; open the index of the stack you write):

<!-- build-index:stacks:start -->
| Writing code for | Open |
|---|---|
| a Bash CLI | [index-frameworks-1.md](references/index-frameworks-1.md) |
| a Go CLI | [index-frameworks-1.md](references/index-frameworks-1.md) |
| a Python MCP server | [index-frameworks-1.md](references/index-frameworks-1.md), [index-frameworks-2.md](references/index-frameworks-2.md) |
| a TypeScript MCP server | [index-frameworks-2.md](references/index-frameworks-2.md) |
| a Node.js CLI | [index-frameworks-2.md](references/index-frameworks-2.md), [index-frameworks-3.md](references/index-frameworks-3.md) |
| a Python CLI | [index-frameworks-3.md](references/index-frameworks-3.md) |
| a Rust CLI | [index-frameworks-3.md](references/index-frameworks-3.md) |
<!-- build-index:stacks:end -->

Not sure which file: the indexes list every page with a one-line "read when".

<!-- build-index:all:start -->
**cli**: [index-cli.md](references/index-cli.md) | **mcp**: [index-mcp-1.md](references/index-mcp-1.md), [index-mcp-2.md](references/index-mcp-2.md), [index-mcp-3.md](references/index-mcp-3.md) | **skill**: [index-skill.md](references/index-skill.md) | **decisions**: [index-decisions.md](references/index-decisions.md) | **frameworks**: [index-frameworks-1.md](references/index-frameworks-1.md), [index-frameworks-2.md](references/index-frameworks-2.md), [index-frameworks-3.md](references/index-frameworks-3.md) | **fresh**: [index-fresh-1.md](references/index-fresh-1.md), [index-fresh-2.md](references/index-fresh-2.md), [index-fresh-3.md](references/index-fresh-3.md)
<!-- build-index:all:end -->

## Evidence instead of opinion

- `/agentic-maker:audit <target>` probes a CLI, script, MCP server or skill and reports against the contract. It changes nothing.
- `/agentic-maker:derail <target>` runs fresh agents on realistic tasks, reads what they did and rewrites the text that misled them.
- `/agentic-maker:design <idea>` interviews you, then sketches the surface before any code.
- `/agentic-maker:build-skill`, `:build-cli` and `:build-mcp` (`<idea or path>`) create or repair a skill, a CLI or an MCP server: grounded in verified facts, written in a fixed order, probed after each stage, then handed over for the fresh-agent test.
