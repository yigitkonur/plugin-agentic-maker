---
as_of: 2026-04
verify_before_citing: true
---
# Model-specific behaviour reported for MCP tool design

> Read when: you need per-model figures behind the MCP rules (tool-response authority, tool-count limits, schema support, enum size); verify before citing any of them.

> `as_of` is inferred from the source corpus's April 2026 refresh: the figures below carry no date of their own, so re-check them before citing.

The source gives no date for these reports; they come from API documentation, community testing and vendor posts. Core rules that depend on them: `../decisions/steering-contract.md`, `../mcp/budget-tool-definitions.md`, `../mcp/schemas-coercion-and-portability.md`, `../mcp/schemas-flat-and-sized.md`.

## Tool-response authority by model

| LLM | Tool result role | vs system prompt | vs user messages |
|-----|-----------------|------------------|------------------|
| Claude | `user` role | Lower | Similar (recency bias) |
| GPT-4 | `tool` role | Lower | Potentially higher (not officially documented) |
| Llama 3 | `tool` role | Lower | Potentially higher (not officially documented) |

In GPT-4 and Llama 3 the dedicated `tool` role may carry elevated authority; in Claude, tool results benefit from recency bias, since the model weighs recent context more heavily when deciding what to do next. Either way tool responses are more effective than system prompts for in-flight guidance.

## Per-model tool limits

| Model | Sweet spot | Hard degradation | Observed behaviour |
|---|---|---|---|
| Claude 3.5 / 4 | 20-30 tools | ~50 tools | Ignores tools beyond position 30; accuracy drops ~15% past 128k context |
| GPT-4 / 4.1 | 15-20 tools | 128 (API hard limit) | Hallucinated tool calls appear above 50; latency roughly doubles above 15 |
| Gemini 1.5 Pro | 10 tools | ~100 tools | Optimised for single-call patterns; measurable quality degradation above 10 |

One vendor explicitly recommends a maximum of 20 tools. The source's illustrative per-model limits in code were `claude: 30`, `gpt-4: 20`, `gemini: 10`, with a universal fallback of 20. Core guidance treats ceilings as cues: up to 20 active tools is comfortable (register them eagerly); past about 20, expose only the tools the task needs (groups or session unlocking); about 30 is a warning; 40 or more needs meta-tools (list, describe, execute). The table above predates that ladder; `tool-count-by-model.md` supersedes it.

## Schema compatibility by model

| Feature | Claude | GPT-4o | Gemini |
|---|---|---|---|
| `oneOf`/`anyOf` | Supported | Supported | Ignored |
| `$ref` references | Supported | Varies | Ignored |
| `format` constraints | Supported | Ignored | Ignored |
| 5+ levels nesting | Supported | Degraded | Breaks |
| Enum > 20 values | Supported | Degraded | Degraded |
| `additionalProperties: false` | Supported | Supported | Supported |

Other reports behind the portability rules: Gemini ignores tools whose schema uses `oneOf`/`anyOf`/`allOf`; GPT-4 degrades beyond 3 levels of nesting; GPT-4 ignores `format: "uri"`; most clients do not resolve `$ref` in tool schemas; GPT models "self-check" on nested schemas and may refuse to call the tool.

## Enum size

> Reconciled: the sources gave 10 (a portability rule: keep enums under 10 values) and 20 (the matrix: enum above 20 values degrades in GPT-4o and Gemini). Core files use 10 inline; above that, describe the values and validate on the server. The 20-value figure is a model-specific report and stays here.

## Call depth by model size

Frontier models handle 20+ sequential tool calls; smaller and open-source models degrade after 5-7 calls (forgotten results, hallucinated parameters, loops). Models named in the source as small: GPT-4o-mini, Haiku, Gemma. Designing for 3-5 calls cuts latency and token cost by 4-10x.

## Description quality and benchmarks

A vendor reported that small, measured refinements to tool descriptions produced large accuracy gains on a coding benchmark (Claude Sonnet 3.5, SWE-bench), with description quality as one of several factors. Community evaluations also report that descriptions over about 200 tokens reduce the tool call rate.
