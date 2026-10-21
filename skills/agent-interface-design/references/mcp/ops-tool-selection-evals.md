# Measure tool selection accuracy across models

> Read when: you want proof that your tool descriptions lead models to pick the right tool with the right parameters, and to keep it true over time.

<!-- src: audit-agentic-mcp/references/patterns/testing.md#5. Use PromptFoo for Systematic Tool Selection Evals -->
## Systematic tool selection evals

The only way to know whether tool descriptions work is to measure tool selection accuracy across models. Use an eval framework (the source uses PromptFoo; see `../fresh/mcp-testing-tools.md` for the config, commands and provider list) to test: given a user intent, does the model pick the right tool with the right parameters?

Design the test cases as pairs:

- **Positive case:** a request that should select a specific tool (for example "Find all orders from last week" should select `search_orders` and include `date_range`). Assert the response contains the tool name and the key parameter.
- **Negative case:** a request that must NOT select the tool (for example "What's the weather today?" must not contain `search_orders`). Assert not-contains.

What to eval:

1. Selection accuracy.
2. Parameter correctness.
3. Ambiguity handling (two tools could apply).
4. Refusal (tools that should not be selected).

Run the evals in CI. A tweak that helps one model can break another, so run the same suite across every model you target. Cross-model behaviour reports (conservative asking before calling, hallucinated parameter values, small models and tool count) are in `../fresh/mcp-testing-tools.md`. Tool count affects selection: up to 20 active tools is comfortable (register them eagerly); past about 20, expose only the tools the task needs; about 30 is a warning; 40 or more needs meta-tools (diagnostic cues, not verdicts; the ladder is in `../decisions/tool-count.md`, per-model caps in `fresh/`). Include a high-tool-count run in the suite.

Sources: Anthropic (writing effective tools for AI agents), PromptFoo MCP integration documentation, r/mcp community discussion.
