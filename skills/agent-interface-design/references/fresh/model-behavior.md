---
as_of: 2026-04-14
verify_before_citing: true
---

# Model-specific tool-use behavior: landscape, conflicts, sources

> Read when: you design an MCP server for several models, pick a default model, or debug a model-specific tool-call failure, and need the benchmark landscape and the conflicts inside the data. All figures retrieved 2026-04-14 and stale by now.

<!-- src: audit-agentic-mcp/references/patterns/model-behavior.md#Model-Specific Tool-Use Behavior and Benchmarks | audit-agentic-mcp/references/patterns/model-behavior.md#The Late-2025 Landscape -->
## The late-2025 landscape

Current-generation empirical per-model reference for MCP server authors (late-2025 frontier and open-weight models). The older "Claude 20-30 / GPT 15-20 / Gemini 10" rules of thumb and the older cross-model schema matrix are superseded by the numbers and idioms in this file family. There is no single tool-use champion; four models lead four leaderboards, and the gap between benchmark wins and production MCP workflows is large.

- **BFCL v3** (single-turn function-calling accuracy): GLM-4.5 leads at 77.8% (https://gorilla.cs.berkeley.edu/leaderboard.html, retrieved 2026-04-14).
- **MCP-Atlas** (real-MCP workflow pass rate across heterogeneous servers): Claude Opus 4.5 leads at 62.3% (https://scale.com/blog/open-sourcing-mcp-atlas and arxiv.org/abs/2602.00933, retrieved 2026-04-14).
- **MCPMark** (multi-step MCP Pass@1): GPT-5 high leads at 57.5% (https://mcpmark.ai/leaderboard, retrieved 2026-04-14).
- **tau2-bench telecom** is effectively saturated at about 99% by GLM-4.7-Flash and GLM-5 Turbo (https://artificialanalysis.ai/evaluations/tau2-bench), so it no longer discriminates; use tau2-airline, MCP-Atlas, and MCPMark.

Three baseline facts:

1. OpenAI's function-calling guide recommends at most 20 active tools (https://platform.openai.com/docs/guides/function-calling, retrieved 2026-04-14).
2. Google's Gemini function-calling docs recommend 10-20 active tools (https://ai.google.dev/gemini-api/docs/function-calling, retrieved 2026-04-14).
3. Microsoft Research (2025-09-11) measured up to 85% accuracy loss from tool-space interference when large tool surfaces are exposed; in a 1,312-tool corpus the top tool averaged 557,766 tokens and 16 tools exceeded 128,000 tokens (cited in Klavis AI, "Function Calling and Agentic AI in 2025", 2025-10-25, https://klavis.ai).

Where the file family lives: `model-behavior-capability-table.md` (per-model table), `model-behavior-idioms.md` (per-family idioms), `model-behavior-rules-tool-surface.md`, `model-behavior-rules-vendor-idioms.md`, `model-behavior-rules-context-and-runtime.md` (the 13 adjustment rules), `model-behavior-cost-and-tiers.md` (tier picks and cost), `tool-count-by-model.md`, and the Zod/Python/TypeScript code in `frameworks/mcp-model-portability-snippets.md`.

## Conflicts

| Item | Claim 1 | Claim 2 |
|---|---|---|
| Active tool cap | Old rule: Claude 20-30, GPT-4 15-20, Gemini 10 (`tool-count-by-model.md`) | Rule 1: at most 20 regardless of vendor |
| Polymorphic schemas on Gemini | Rule 2: emit `oneOf` via `discriminatedUnion()`, Gemini handles it | Capability table and Rule 6: Gemini rejects `anyOf` and `$ref`; use `oneOf` only on OpenAI-strict or DeepSeek paths; Rule 13: prefer `action` enums |
| Enum size | Rule 6 snippet: `enum` over 20 values degrades all non-Claude models | Note below: inline enums up to 10 values |
| Qwen3 on BFCL | Idioms: Qwen3 tops BFCL v3 single-turn aside from GLM | Table: Qwen3-Coder 480B scores 68.7%, below Claude Sonnet 4 (70.3%) and Opus 4.1 (70.4%) |
| Prompt-cache saving | Rule 3: "roughly 83%" over a multi-turn session | Its own prices give about 71% over 10 requests, 83% only near 30 requests |
| GPT-5 mini cost | Cost table: "about 10x cheaper than GPT-5" | Its own prices: $1.25 vs $0.25 input, $10 vs $2 output, about 5x |
| Flash pass rate | Cost picks: "3-9% MCP-Atlas pass rate" | Table: 3.4% is MCP-Atlas, 9.1% is MCPMark |

> Note: avoid `oneOf`/`anyOf` at the top of an input schema, inline enums up to 10 values, and above that describe the values and validate on the server. The enum over 20 claim is a model-specific report. Tool counts: `decisions/tool-count.md`.

> Unresolved: the Qwen3 BFCL claim contradicts the table; both are kept as reported.

<!-- src: audit-agentic-mcp/references/patterns/model-behavior.md#Quick Cross-Reference to Sibling Patterns -->
## Cross-reference to sibling patterns

- Tool count, progressive discovery: `decisions/tool-count.md`, `mcp/budget-*`, read with Rule 1.
- Schema portability: `mcp/schemas-*`, extended by Rules 2, 6, 13.
- Context budget math: `mcp/budget-*`; its per-model tool cliffs are superseded by Rules 1, 7, 8, 9.
- Error-shape guidance for retries: `mcp/errors-*` (Rule 12).
- Facade/action-routed tools: `mcp/design-*` (Rule 13).

<!-- src: audit-agentic-mcp/references/patterns/model-behavior.md#Key Sources -->
## Key sources

BFCL v3: gorilla.cs.berkeley.edu/leaderboard.html. tau2-bench: taubench.com, hal.cs.princeton.edu/taubench_airline, artificialanalysis.ai/evaluations/tau2-bench, sierra.ai/blog/t-bench-leaderboard. MCP-Atlas: scale.com/blog/open-sourcing-mcp-atlas (arxiv.org/abs/2602.00933). MCPMark: mcpmark.ai/leaderboard. Anthropic parallel tools: platform.claude.com/docs/en/agents-and-tools/tool-use/parallel-tool-use; prompt caching: platform.claude.com/docs/en/build-with-claude/prompt-caching; Opus 4.5 launch (2025-11-24). OpenAI function calling: platform.openai.com/docs/guides/function-calling; structured outputs: developers.openai.com/api/docs/guides/structured-outputs; GPT-5 freeform tool calling (2025-08-22): devblogs.microsoft.com/foundry/unlocking-gpt-5s-freeform-tool-calling-a-new-era-of-seamless-integration/. Gemini: ai.google.dev/gemini-api/docs/function-calling; Zod `anyOf` bug: github.com/colinhacks/zod/issues/5807. DeepSeek: api-docs.deepseek.com/guides/function_calling. Klavis AI 2025 analysis (2025-10-25); Microsoft Research tool-space interference (2025-09-11, as cited by Klavis); Chroma 2025 "Context Rot" study; Glean Sonnet 4.5 efficiency measurements (2026-01-27). All URLs and dated measurements retrieved on 2026-04-14.
