---
as_of: unknown
verify_before_citing: true
---

# Source-reported figures from the MCP decision trees

> Read when: you need the token and throughput figures the decision trees quoted (concise vs detailed responses, session pooling, initial-context size under progressive discovery) and want to know they are undated.

The decision trees in `decisions/` quote these figures without a date or a method. Treat each as a source-reported estimate, re-measure on your own server (`bin/agentic-maker probe mcp --budget` for tool-catalog size), and do not cite as a benchmark.

## Response format (`decisions/response-format.md`)

- concise response: about 72 tokens per response; detailed response: about 206 tokens per response.
- Defaulting to concise: 65% token reduction.

## Scaling (`decisions/scaling.md`)

- Session pooling (shared pool of 10 sessions): 30 req/s with unique sessions became 300 req/s pooled.
- Factor table: session pooling gives about a 10x throughput improvement.

## Tool count (`decisions/tool-count.md`)

- 40-100 tools with meta-tools (`list_tools` / `describe_tools` / `execute_tool`): initial context about 1.5-2.5k tokens, against 40k+ for a static list.
- 100+ tools with semantic search (`find_tools(query)` plus `execute_tool`): about 1.3k initial tokens, best for simple single-intent queries.
- On-demand schema loading saves 95%+ of tokens at 100+ tools.
