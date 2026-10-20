---
as_of: 2026-04-14
verify_before_citing: true
---

# Model capability table: benchmarks, schema caveats, pricing

> Read when: you need one row per model with its tool-use benchmark scores, parallel-call behavior, JSON Schema caveats, and prices. Landscape and conflicts: `model-behavior.md`.

<!-- src: audit-agentic-mcp/references/patterns/model-behavior.md#Master Model-Capability Table -->
## Master model-capability table

All benchmark scores were retrieved 2026-04-14. Pricing in USD per 1M tokens; "Cache hit" is the input-cached read price where publicly documented. tau2 = tau2-bench airline.

| Model | Release | BFCL v3 | tau2 airline | MCP-Atlas pass | MCPMark Pass@1 | Parallel tools | JSON Schema caveats | Input $/M | Output $/M | Cache hit $/M |
|---|---|---|---|---|---|---|---|---|---|---|
| Claude Opus 4.5 | 2025-11-24 | n/a | n/a | **62.3%** | 42.3% | Default on | Full JSON Schema | $5 | $25 | $0.50 |
| Claude Sonnet 4.5 | 2025-09-29 | n/a | n/a | 43.8% | 32.1% | Default on | Full | $3 | $15 | $0.30 |
| Claude Sonnet 4 | 2025-05 | 70.3% | 44.0% | 35.6% | 28.1% | Default on | Full | $3 | $15 | $0.30 |
| Claude Opus 4.1 | 2025-08 | 70.4% | 54.0% | 40.9% | 29.9% | Default on | Full | $15 | $75 | $1.50 |
| Claude Haiku 4.5 | 2025-10-15 | n/a | n/a | n/a | n/a | Default on | Full | $1 | $5 | $0.10 |
| Claude 3.7 Sonnet | 2025-02 | n/a | 56.0% | n/a | n/a | Default on | Full | $3 | $15 | $0.30 |
| GPT-5 | 2025-08-07 | 59.2% | 48.0% | 44.5% | **57.5%** high | Default on | Strict: oneOf/anyOf/allOf/$ref OK; freeform mode bypasses JSON | $1.25 | $10 | $0.125 |
| GPT-5 mini | 2025-08-07 | n/a | n/a | n/a | 27.4-30.3% | Yes | Same as GPT-5 | ~$0.25 | ~$2 | ~$0.025 |
| GPT-4.1 | 2025-04-14 | n/a | 36-68% | n/a | 8.1% | Yes; nano duplicate-call bug | Strict: `additionalProperties:false` + every field required | $2 | $8 | $0.50 |
| o3 medium | 2025-04 | n/a | 54.0% | 43.6% | 25.4% | Yes | Same as GPT-5 strict | ~$2 | ~$8 | none |
| o4-mini high | 2025-04 | n/a | 56.0% | n/a | 17.3% | Yes | Same | ~$1.1 | ~$4.4 | none |
| Gemini 3 Pro Preview | 2025-11 | n/a | n/a | **54.1%** | 53.9% | Yes | No `anyOf`; no `$ref`; rejects deep nesting | $2 | $12 | $0.20 |
| Gemini 2.5 Pro | 2025-03 | n/a | n/a | 8.8% | 15.8% | Yes | Same Gemini limits | $1.25 / $2.50 >200k | $10 / $15 >200k | $0.125 |
| Gemini 2.5 Flash | 2025 | n/a | n/a | 3.4% | 9.1% | Yes | Same | $0.30 | $2.50 | $0.03 |
| Grok 4 | 2025-07-09 | n/a | n/a | n/a | 31.7% | Advertised; undocumented | None published | $3 | $15 | $0.75 |
| Llama 4 Maverick | 2025-04-05 | n/a | n/a | **0.8%** | n/a | Partial | No first-party tool-use training | ~$0.20 / $0.60 | none | none |
| Llama 4 Scout | 2025-04-05 | 55.7% | n/a | n/a | n/a | Partial | Same | none | none | none |
| GLM-4.5 | 2025 | **77.8%** (#1) | n/a | n/a | 15.6% | Yes | none | $0.40 | $1.60 | none |
| Qwen3-Max | 2025 | n/a | n/a | 12.0% (235B) | 17.7% | Yes | `enum` OK; oneOf/$ref undocumented | ~$0.15 | ~$3 | none |
| Qwen3-Coder-Plus | 2025 | 480B: 68.7% | n/a | n/a | 24.8% | Yes | Same | ~$0.30 | ~$1.50 | none |
| DeepSeek V3.2 thinking | 2025 | n/a | n/a | n/a | 36.8% | Yes (single-user-msg-many-calls idiom) | Strict: `anyOf` + `$ref` supported | $0.27 / $0.07 cache | $1.10 | $0.07 |
| DeepSeek R1 | 2025-01 | n/a | 36.0% | n/a | n/a | R1-0528 improved tools | Same | $0.55 / $0.14 cache | $2.19 | $0.14 |
| Mistral Large 2 (2024-11) | n/a | n/a | n/a | n/a | n/a | `parallel_tool_calls=true` default | Only `type/object/properties/required/string` | $2 | $6 | none |

Source index: BFCL gorilla.cs.berkeley.edu/leaderboard.html; tau2-airline hal.cs.princeton.edu/taubench_airline and sierra.ai/blog/t-bench-leaderboard; tau2 live artificialanalysis.ai/evaluations/tau2-bench; MCP-Atlas scale.com/blog/open-sourcing-mcp-atlas (arxiv 2602.00933); MCPMark mcpmark.ai/leaderboard; pricing via llm-stats.com and pricepertoken.com; Klavis AI 2025-10-25 analysis at klavis.ai. All retrieved 2026-04-14. "none" replaces the source's dash (no figure published in the source).
