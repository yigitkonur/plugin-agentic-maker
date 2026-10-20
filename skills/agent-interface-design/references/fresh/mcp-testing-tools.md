---
as_of: 2026-07-04
verify_before_citing: true
---
# MCP testing tools, model identifiers and cross-model reports

> Read when: you need the concrete Inspector launch command, an eval framework config, model identifiers used in the examples, or reports of how different models behave in tool selection.

No date is given for these items; verify every command, package name, model identifier and behaviour report before citing.

<!-- src: audit-agentic-mcp/references/patterns/testing.md#2. Test Tools with MCP Inspector Before Involving an LLM -->
## MCP Inspector

Launch command and default address:

```bash
npx @modelcontextprotocol/inspector@latest
# Opens http://localhost:5173
```

Package: `@modelcontextprotocol/inspector` (npm). Use it for the checks in `../mcp/ops-testing-layers.md`.

<!-- src: audit-agentic-mcp/references/patterns/testing.md#1. Use Evaluation-Driven Development with Realistic Multi-Step Tasks -->
## Model identifiers in the source examples

- Eval loop example model: `claude-sonnet-4-20250514` (see `../frameworks/mcp-python/testing.md`).
- PromptFoo providers: `openai:gpt-4o`, `anthropic:messages:claude-sonnet-4-20250514`, `ollama:llama3.1`.

<!-- src: audit-agentic-mcp/references/patterns/testing.md#5. Use PromptFoo for Systematic Tool Selection Evals -->
## PromptFoo config for tool selection evals

```yaml
# promptfoo.yaml
prompts:
  - "You have access to these tools: {{tools}}. User request: {{request}}"

providers:
  - openai:gpt-4o
  - anthropic:messages:claude-sonnet-4-20250514
  - ollama:llama3.1

tests:
  # Positive case: correct tool should be selected
  - vars:
      request: "Find all orders from last week"
      tools: "{{tool_schemas}}"
    assert:
      - type: contains
        value: "search_orders"
      - type: contains
        value: "date_range"

  # Negative case: tool should NOT be selected
  - vars:
      request: "What's the weather today?"
      tools: "{{tool_schemas}}"
    assert:
      - type: not-contains
        value: "search_orders"
```

Run it:

```bash
npx promptfoo@latest eval
npx promptfoo@latest view  # opens comparison dashboard
```

Documentation: https://www.promptfoo.dev/docs/integrations/mcp/

## Cross-model gotchas (model-specific report)

- Claude is conservative (asks before calling).
- GPT hallucinates parameter values.
- Smaller models (Llama, Mistral) struggle with more than 10 tools.
- A tweak that helps Claude can break Llama, so run evals in CI.

> Note: the 10-tool figure is a model-specific report for small models. The general tool-count cues are in `../mcp/ops-tool-selection-evals.md`: up to 20 active tools is comfortable (register them eagerly); past about 20, expose only the tools the task needs (groups or session unlocking); about 30 is a warning; 40 or more needs meta-tools (list, describe, execute).

## Source threads

Selection-eval approach discussed on r/mcp; framing from https://www.anthropic.com/engineering/writing-tools-for-agents; Inspector at https://www.npmjs.com/package/@modelcontextprotocol/inspector.
