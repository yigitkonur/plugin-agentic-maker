---
as_of: 2026-04-14
verify_before_citing: true
---

# Model tier picks and reference-workload cost

> Read when: you choose a model tier for an MCP host or estimate cost per session with and without prompt caching. Prices and scores are from 2026-04-14 or earlier and stale.

<!-- src: audit-agentic-mcp/references/patterns/model-behavior.md#Pattern 10: Pick model tier by real-MCP benchmarks (MCP-Atlas / MCPMark), not BFCL -->
## Rule 10: Pick model tier by real-MCP benchmarks (MCP-Atlas / MCPMark), not BFCL

BFCL v3 measures single-turn function-calling accuracy; winning it does not imply winning real MCP workflows. GLM-4.5 tops BFCL at 77.8% but scores only 15.6% on MCPMark Pass@1. Use MCP-Atlas and MCPMark for production tier decisions:

- Quality-first MCP host: Claude Opus 4.5 (62.3% MCP-Atlas).
- Balanced cost/quality: GPT-5 high (57.5% MCPMark) or Gemini 3 Pro (54.1% MCP-Atlas).
- Budget executor under a stronger planner: Claude Haiku 4.5, GPT-5 mini, or DeepSeek V3.2 thinking (36.8% MCPMark at about $0.27/M input).

Source: scale.com/blog/open-sourcing-mcp-atlas; mcpmark.ai/leaderboard.

<!-- src: audit-agentic-mcp/references/patterns/model-behavior.md#Cost Analysis: Reference Workloads -->
## Cost analysis: reference workloads

Assumptions: 20 active tools, 10-step average conversation, 30K static context (system + tool definitions), 1K tool-result tokens per turn, 2K output tokens per turn, 10 sessions. Prices from `model-behavior-capability-table.md`. "Best cache" uses each provider's documented mechanics (Claude 1h prompt cache, OpenAI implicit cache, Gemini context cache, DeepSeek cache-hit pricing).

| Model | No caching | With best cache | Notes |
|---|---|---|---|
| Claude Sonnet 4.5 | ≈ $4.05 | ≈ $2.00 (1h tool-block cache saves ~$2.05) | Strongest when MCP surface is stable and session-bursty |
| Claude Opus 4.5 | ≈ $6.75 | ≈ $3.35 | Use when Opus-quality arbitration and 65-76% output compression pay for themselves |
| Claude Haiku 4.5 | ≈ $1.35 | ≈ $0.90 | Cheapest Anthropic route; ideal executor under an Opus planner |
| GPT-5 | ≈ $2.06 | ≈ $1.50 (implicit cache) | Very strong with freeform mode on code/DSL tools |
| GPT-5 mini | ≈ $0.41 | ≈ $0.30 | About 5x cheaper than GPT-5; useful as a default for non-critical sessions |
| Gemini 2.5 Pro | ≈ $2.06 | ≈ $1.30 (context cache ≥10 min) | Watch per-hour storage fee on long idle caches |
| Gemini 2.5 Flash | ≈ $0.51 | ≈ $0.35 | Cheapest top-tier, but accept 3.4% MCP-Atlas |
| DeepSeek V3.2 thinking | ≈ $0.34 | ≈ $0.22 | Best price/quality for single-turn-many-call idiom |
| Grok 4 | ≈ $4.05 | ≈ $2.75 | No public MCP benchmark; measure before committing |
| Llama 4 Maverick (Fireworks) | ≈ $0.23 | no standard cache | MCP-Atlas 0.8%, plan for heavy scaffolding |

> Reconciled: the source called GPT-5 mini "~10x cheaper than GPT-5"; its own prices and totals ($0.41 vs $2.06; $0.25 vs $1.25 input) give about 5x, which this file uses.

Three concrete picks:

- **Cheap broad-MCP:** Gemini 2.5 Flash at about $0.35 per 10 sessions, only if you can tolerate the low pass rates (3.4% MCP-Atlas, 9.1% MCPMark; the source wrote "3-9%") and you have hard-flattened schemas.
- **Best quality/dollar for real MCP workflows:** GPT-5 + caching + freeform tool calling at about $1.50 per 10 sessions with 57.5% MCPMark Pass@1.
- **Best absolute quality:** Claude Opus 4.5 at about $3.35 cached per 10 sessions with 62.3% MCP-Atlas, amplified by the 65-76% output-token reduction over Sonnet 4.5.
