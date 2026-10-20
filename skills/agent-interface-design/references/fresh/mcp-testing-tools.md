---
as_of: unknown
verify_before_citing: true
---
# MCP testing tools, model identifiers and cross-model reports

> Read when: you need the concrete Inspector launch command, an eval framework config, model identifiers used in the source examples, or reports of how different models behave in tool selection.

The source gives no date for these items; verify every command, package name, model identifier and behaviour report before citing.

<!-- src: audit-agentic-mcp/references/patterns/testing.md#2. Test Tools with MCP Inspector Before Involving an LLM -->
## MCP Inspector

Launch command and default address from the source:

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

> Reconciled: the sources gave a "more than 10 tools" report for small models here and the brief's tool-count cues (up to 20 comfortable, about 30 warning, 40 or more needs progressive discovery); this file keeps the 10-tool figure as a model-specific report only and `../mcp/ops-tool-selection-evals.md` states the general cues.

## Source threads

Selection-eval approach discussed on r/mcp; framing from https://www.anthropic.com/engineering/writing-tools-for-agents; Inspector at https://www.npmjs.com/package/@modelcontextprotocol/inspector.
