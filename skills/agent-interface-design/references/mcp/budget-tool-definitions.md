# Context budget: tool definitions, code-execution discovery, tool limits

> Read when: tool definitions are eating context, the tool list keeps growing, or you must decide between trimming, lazy discovery and a code-execution gateway.

<!-- src: audit-agentic-mcp/references/patterns/context-engineering.md#Context Engineering Patterns -->
Patterns for optimizing token use and cutting the hidden cost of MCP tool definitions. Response-size patterns (tiered verbosity, ANSI stripping, pagination) are in `budget-response-size.md`; provider prompt caching is in `budget-cache-stable-prefix.md`. Code: `../frameworks/mcp-python/context-engineering.md`, `../frameworks/mcp-ts/context-engineering.md`.

Measure before and after: run `agentic-maker probe mcp --budget` against the real `tools/list` response when you trim descriptions, schema blocks or static response examples. The retired helper script used a chars/4 token estimate and flagged more than 20 active tools by default; keep those two numbers as the rough heuristic when you cannot probe.

<!-- src: audit-agentic-mcp/references/patterns/context-engineering.md#1. Tool Descriptions Eat ~15% of Your Context Budget -->
## Tool definitions are a recurring cost

Every registered tool injects its full definition (name, description, input schema) into the system prompt on **every single message**, not only when the tool is invoked. Community measurements put definitions at a large share of a coding agent's input tokens, and one complex tool server alone can take half (figures: `../fresh/mcp-token-benchmarks.md`).

The math compounds: each definition costs 50-150 tokens depending on schema complexity. Twenty tools at 100 tokens is 2,000 tokens per message; across a 30-turn conversation that is 60,000 tokens spent on definitions alone. Client tools to inspect the breakdown: `../fresh/mcp-client-and-sdk-quirks.md`.

Example: a description of `search_documents` of about 55 tokens (219 characters) ("Searches through all documents in the repository using full-text search. Supports boolean operators, phrase matching, and field-specific queries. Returns paginated results with relevance scores and highlighted snippets.") becomes "Full-text search across repo docs. Supports boolean, phrase, field queries. Returns paginated results." (about 25 tokens, 102 characters, same capability). Budget audit rule: estimate tokens as characters / 4 and flag a description above about 100 tokens (Low) and above 200 (Medium), which is what `probe mcp` does (`--description-chars`, default 400 characters); the whole definition, schema included, typically costs 50-150 tokens. Length guidance: `descriptions-structure-and-length.md`.

Trimming descriptions is one of the highest-ROI context optimizations: no architecture change, and it compounds over the whole conversation.

<!-- src: audit-agentic-mcp/references/patterns/context-engineering.md#2. The Code Execution Pattern Saves 98% of Tool-Related Tokens -->
## Code-execution discovery saves most tool-definition tokens

Instead of registering every definition upfront, expose one `execute_code(code, language="python")` tool that runs scripts in a sandbox. Inside it the model calls `list_servers()` (names only), then `list_tools(server)` (names plus one-line summaries, 80 characters), then `get_tool_schema(server, tool)` only when it needs a specific tool, then `call_tool(server, tool, args)`. Full schemas are fetched on demand and discarded after the call, never injected permanently. Reported savings are large (benchmarks: `../fresh/mcp-token-benchmarks.md`).

Production caveat: this works cleanly with stdio-based local servers, but most production deployments use remote HTTP/SSE servers where OAuth flows and session management make dynamic discovery more complex. Sandbox security requirements: `design-workflow-planner-and-facade.md`. Alternatives for big catalogs: `patterns-progressive-discovery.md`.

<!-- src: audit-agentic-mcp/references/patterns/context-engineering.md#6. Each LLM Has a Tool Limit Beyond Which Accuracy Collapses -->
## Models have a tool limit; keep the roster small

Registering more tools does not make a model more capable; past a model-specific threshold it makes it less capable, and degradation looks like a cliff, not a slope. Per-model profiles (sweet spot, hard degradation, observed behaviour) are model-specific reports and live in `../fresh/mcp-model-behavior.md`. One vendor recommends at most 20 tools; community consensus: "There is no standard solution. Disable the ones you don't need."

> Note: treat tool-count ceilings as diagnostic cues, not verdicts. Up to 20 active tools is comfortable (register them eagerly); past about 20, expose only the tools the task needs (groups or session unlocking); about 30 is a warning; 40 or more needs meta-tools (list, describe, execute). Per-model caps live in `../fresh/mcp-model-behavior.md`; decision tree in `../decisions/tool-count.md`.

Tactics:
- **Tool groups:** keep a registry mapping a task type to its tools (`code-review`: `read_file`, `search_code`, `get_diff`, `add_comment`; `deployment`: `run_pipeline`, `get_logs`, `rollback`, `set_env`; `data-analysis`: `query_db`, `export_csv`, `run_notebook`, `plot_chart`) and expose only the relevant group; fall back to a safe universal cap of 20.
- **Progressive disclosure:** start with 3 always-on tools (`help`, `search`, `read_file`) and expand on request up to a per-model limit.

Every tool past the model's sweet spot adds token cost and degrades routing accuracy; tool roster hygiene is a first-class correctness concern. Changing the roster mid-session has a cache cost: `patterns-dynamic-tool-lists.md`.
