# Evaluate tools with realistic multi-step tasks

> Read when: you are building an evaluation suite for an MCP server or turning eval transcripts into description and schema fixes.

<!-- src: audit-agentic-mcp/references/patterns/testing.md#1. Use Evaluation-Driven Development with Realistic Multi-Step Tasks -->
## Evaluation-driven development

Do not test MCP tools in isolation. Build an evaluation suite that tests complete user workflows through the agent-tool interaction loop.

The eval loop: send the task prompt to a model with the server's tools and a system prompt such as "You are testing MCP tools. Think step by step before each tool call." Loop: if the stop reason is `end_turn`, score the run; otherwise execute each requested tool call against the server, append the assistant content and a `tool_result` user message (carrying the `tool_use_id`), and continue. A run returns `success` (verified against ground truth), `tool_calls`, `tokens_used` (input plus output) and the full `transcript`. Python code: `../frameworks/mcp-python/testing.md`. Model identifiers: `../fresh/mcp-testing-tools.md`.

What to measure beyond accuracy:

- Total number of tool calls (fewer is better design).
- Token consumption per task.
- Error rate and recovery rate.
- Time to completion.
- Whether the model chose the right tool on the first try.

Pro tip, chain of thought before tool calls: include reasoning or feedback blocks in the system prompt before any tool-call block to trigger chain-of-thought. This surfaces the model's decision-making and helps you spot tool selection confusion.

Pro tip, auto-refactoring: feed the full evaluation transcript back to the model and ask it to suggest description tweaks, parameter clarifications and schema fixes based on where it struggled (next section).

Sources: Anthropic (writing effective tools for AI agents), the MCP documentation on effective tools.

<!-- src: audit-agentic-mcp/references/patterns/testing.md#3. Feed Evaluation Transcripts Back for Auto-Refactoring -->
## Feed transcripts back for auto-refactoring

After running evaluation tasks, concatenate the full tool-call transcripts and feed them back to the model. It can spot description ambiguities, schema inconsistencies and naming issues that humans miss.

The workflow: (1) run the eval and capture, per task, the `task` description, `success`, `transcript`, `tool_calls` and `tokens`; (2) send the collected results to the model with a request to analyze them and, for each failure or inefficiency, identify:

1. Which tool description was ambiguous.
2. What parameter naming caused confusion.
3. Where the response format led the model astray.
4. Specific text changes to fix each issue.

Ask for the output as a structured list of changes to make. Code: `../frameworks/mcp-python/testing.md`.

What the model typically catches:

- Tool descriptions that overlap, causing selection confusion.
- Parameter names that do not match how the model thinks about the concept.
- Missing examples in descriptions that would prevent common mistakes.
- Response formats that bury important information.
- Error messages that do not provide actionable recovery guidance.

Iterate until stable: repeat the prototype, evaluate, refine cycle until held-out test set performance stabilizes. Typically 3-5 rounds are enough.

Sources: Anthropic (writing effective tools for AI agents), the MCP documentation on effective tools.
