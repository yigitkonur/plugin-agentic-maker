---
as_of: 2026-04-14
verify_before_citing: true
---

# Per-family tool-call idioms

> Read when: a tool-calling failure appears on one model family (Claude, GPT, Gemini, Llama 4, Qwen 3, DeepSeek, Mistral, Grok) and you need the call-shape idiom that family prefers.

These are the details that break MCP clients when left wrong, not the ones benchmarks capture. Scores and prices: `model-behavior-capability-table.md`.

<!-- src: audit-agentic-mcp/references/patterns/model-behavior.md#Per-Family Idioms -->
## Per-family idioms

<!-- src: audit-agentic-mcp/references/patterns/model-behavior.md#Claude (4, 4.5, 4.6) -->
### Claude (4, 4.5, 4.6)

- Parallel tool use is default-on starting with the 4.x family (platform.claude.com/docs/en/agents-and-tools/tool-use/parallel-tool-use).
- All `tool_result` blocks for a parallel batch must be in a single subsequent user message. Splitting them across messages is the number one Claude parallel-call bug in the wild.
- Disable parallel tool use when strict step-by-step is required: set `disable_parallel_tool_use=true` inside `tool_choice`.
- Sonnet 4.5 converges faster than Sonnet 4 on agentic loops per Glean (2026-01-27): 1.61 tool calls/turn (vs 2.08), 1.34 parallel calls/turn (vs 1.00), 2.19 adaptive-planning cycles (vs 3.08).
- Prompt cache is the biggest MCP cost lever. Up to 4 cache breakpoints, 20-block lookback, 1h extended TTL at 2x base input on write and 10% of base on hit (platform.claude.com/docs/en/build-with-claude/prompt-caching).
- Opus 4.5 produces 65-76% fewer output tokens at equal quality vs Sonnet 4.5 (Anthropic 2025-11-24 launch post), which matters when the tool loop emits long assistant messages.

<!-- src: audit-agentic-mcp/references/patterns/model-behavior.md#GPT (5, 4.1, o3, o4-mini) -->
### GPT (5, 4.1, o3, o4-mini)

Two tool-calling modes:

1. **Classic JSON tool calls**, optionally `strict: true`. Strict mode supports `oneOf`/`anyOf`/`allOf`/`$ref` but requires `additionalProperties: false` and every field in `required` (use a nullable type for optional). See developers.openai.com/api/docs/guides/structured-outputs.
2. **Freeform tool calling (GPT-5 only, 2025-08-22)**: raw text payloads, no JSON. Result comes back via `function_call_output`. Best for shells, code, SQL, regex, DSLs (devblogs.microsoft.com/foundry/unlocking-gpt-5s-freeform-tool-calling-a-new-era-of-seamless-integration/).

OpenAI's own guidance: "aim for fewer than 20 functions at any one time". `gpt-4.1-nano-2025-04-14` has a duplicate-call bug with parallel tool calls: disable parallel on that model specifically. Reasoning items returned alongside tool calls must be round-tripped on the next request or behavior degrades.

<!-- src: audit-agentic-mcp/references/patterns/model-behavior.md#Gemini (2.5, 3) -->
### Gemini (2.5, 3)

- Parallel function calling supported across 2.5 and 3.
- `anyOf` not supported in function calling; confirmed by the Zod issue colinhacks/zod #5807 (2026-03). Substitute `discriminatedUnion()` so Zod emits `oneOf`, which Gemini handles (see the conflict in `model-behavior.md`).
- `$ref` not supported.
- The API rejects "very large or deeply nested schemas": flatten to at most 3 levels, keep property names under 20 chars.
- Google recommends at most 10-20 active tools (ai.google.dev/gemini-api/docs/function-calling).
- Context caching is priced per hour of storage ($4.50 per 1M tokens per hour on 2.5 Pro), unusual among providers. Estimate storage-hours, not just read count.

<!-- src: audit-agentic-mcp/references/patterns/model-behavior.md#Llama 4 -->
### Llama 4

No first-party function-calling training. The ecosystem uses Hermes-style tags (Nous Research) or host adapters. MCP-Atlas 0.8% for Maverick is the lowest among frontier models, so plan for heavy scaffolding (explicit planner tool, tight tool shapes, examples in descriptions) if you must support Llama 4.

<!-- src: audit-agentic-mcp/references/patterns/model-behavior.md#Qwen 3 -->
### Qwen 3

Native Hermes-style tool use; vLLM + Qwen-Agent emit multiple `tool_calls` in one assistant message. Qwen3 tops BFCL v3 single-turn (aside from GLM) but falls off on multi-step MCP (Qwen3-Max 17.7% MCPMark). Schema-wise, `enum` is safe; `oneOf`/`anyOf`/`$ref` are not documented, so assume unsupported.

<!-- src: audit-agentic-mcp/references/patterns/model-behavior.md#DeepSeek (V3, R1, V3.2) -->
### DeepSeek (V3, R1, V3.2)

- DeepSeek never published an official chat template for tool use; Fireworks reverse-engineered one in their 2025-02-14 blog, which is why many hosts still hit parser fragility. Pin provider hosting.
- DeepSeek's own docs state the model is "not great at multi-turn function calling" and performs best with one user message triggering multiple tool calls in a single assistant turn (api-docs.deepseek.com/guides/function_calling).
- R1-0528 (May 2025) ships tool-calling fixes: use R1-0528 or newer, never pre-0528.
- Strict mode supports `object/string/number/integer/boolean/array/enum/anyOf/$ref/$def`, making DeepSeek the most JSON-Schema-friendly provider aside from OpenAI strict.

<!-- src: audit-agentic-mcp/references/patterns/model-behavior.md#Mistral -->
### Mistral

`parallel_tool_calls: true` is default. Flip to `false` for single-tool discipline. Schema support is minimal: only `type/object/properties/required/string`; no `oneOf`/`anyOf`/`$ref`/`format`.

<!-- src: audit-agentic-mcp/references/patterns/model-behavior.md#Grok (xAI) -->
### Grok (xAI)

Neither Grok 4's release post nor model card publishes BFCL, tau-bench, or MCP numbers. Treat Grok as `no-public-benchmark-2025-12`. MCPMark reports Grok 4 at 31.7% Pass@1. Advertised features include agentic tool calling, cached-token pricing, and remote MCP tools, but parallel-call semantics are undocumented: test empirically before relying on them.
