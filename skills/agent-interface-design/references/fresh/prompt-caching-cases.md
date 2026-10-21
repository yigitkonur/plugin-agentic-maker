---
as_of: 2026-04
verify_before_citing: true
---
# Prompt-caching case studies and incidents

> Read when: you need published numbers for what prompt caching saved, or the incident behind a caching rule (default TTL flip, one-letter prefix change, tool-list changes); verify before citing.

Real numbers from published post-mortems dated 2024-10 to 2026-04; use them as upper-bound references, not promises. Rules: `../mcp/budget-cache-stable-prefix.md`, `../mcp/budget-cache-ttl-and-monitoring.md`. Links: `prompt-caching-sources.md`.

## Evidence quoted inside the patterns

- A single capitalization change ("senior" to "Senior") in a coding agent's system prompt invalidated 2,727 cached tokens (2026-02-25).
- That agent forbids post-session tool registration, because adding or removing a tool rewrites the tools block; its deferred-loading strategy for tool stubs is the canonical reference (2026-02-25).
- ProjectDiscovery moved volatile working memory out of the prefix into a tail user message; hit rate went 7% to 84% and the bill fell 59% (2026-04-10). It froze datetime to date-only as one of five changes, and pins the vendor's direct API first, falling back to cloud marketplaces only during outages, which kept the hit rate steady during the 1M-context rollout.
- The default-TTL flip and its cost are Case 6 below (issue filed 2026-04-12).

<!-- src: audit-agentic-mcp/references/patterns/caching-economics.md#Case Studies -->
## Case studies

<!-- src: audit-agentic-mcp/references/patterns/caching-economics.md#Case 1 — ProjectDiscovery "Neo" agent: 7% → 84% hit rate, −59% cost -->
### Case 1: ProjectDiscovery "Neo" agent, 7% to 84% hit rate, -59% cost

Five compounding changes:
1. Relocated dynamic content from the system prompt into a tail user message.
2. Switched the system prompt and tool block to 1h TTL.
3. Froze datetime to `YYYY-MM-DD`.
4. Reordered tools so static tools come first; put `cache_control` on the last static tool; dynamic subagent tools after.
5. Pinned the vendor's direct API as the primary route.

Aggregate: overall cost -59%; last 10 days -70%; 9.8B tokens served from cache. Complex tasks (20+ steps, 3.7M average input tokens) hit 74% cache rates. Extreme tasks hit 91.8% on 67.5M tokens across 1,225 steps (published 2026-04-10).

<!-- src: audit-agentic-mcp/references/patterns/caching-economics.md#Case 2 — Bifrost "Code Mode" with 508 MCP tools: 92% cost reduction -->
### Case 2: Bifrost "Code Mode" with 508 MCP tools, 92% cost reduction

Baseline: 508 MCP tools, 75.1M input tokens, **$377/run**. After switching to code-execution mode (no tool schemas sent; the model writes code against a lightweight tool index): 5.4M tokens, **$29/run**, 100% test pass. Savings scale with tool count: 96 tools 58%, 251 tools 84%, 508 tools 92% (community thread, 2025-11).

<!-- src: audit-agentic-mcp/references/patterns/caching-economics.md#Case 3 — Claude Code practical session: 96% hit rate, ~80% cheaper -->
### Case 3: Claude Code practical session, 96% hit rate, about 80% cheaper

A 100-turn Opus coding session that would cost **$50-100** without caching runs at **$10-19** with caching. Documented 96% hit rate. A single-case change ("senior" to "Senior") invalidated 2,727 cached tokens. The agent reuses about 18K tokens of prefix cache across compaction and fork operations (2026-02-25).

<!-- src: audit-agentic-mcp/references/patterns/caching-economics.md#Case 4 — MCP caching SaaS rebuild: 73% per-analysis cost cut -->
### Case 4: MCP caching SaaS rebuild, 73% per-analysis cost cut

Full stack: prompt caching + L1 in-memory + L2 Redis + data-type-specific TTLs (stock quote 300s, financials 86400s, SEC filings 604800s). Per-analysis API cost **$0.40 to $0.11 (-73%)**. One write-up also claims **$912,500/year saved** at enterprise scale (1M requests/day); that figure does not follow from the per-analysis cost ($0.29 saved x 1M x 365 is about $106M), so its basis is unstated and it is not a number to plan with. Cache-hit latency 84ms; miss 256ms (2025-10-14).

<!-- src: audit-agentic-mcp/references/patterns/caching-economics.md#Case 5 — Long-horizon agent benchmark (arXiv 2601.06007v2, 2026-01) -->
### Case 5: Long-horizon agent benchmark (arXiv 2601.06007v2, 2026-01)

500 agent sessions x 10,000-token system prompts:

| Model | Cost savings | TTFT improvement |
|---|---|---|
| Claude Sonnet 4.5 | 78.5% | 22.9% |
| GPT-5.2 | 79.6% | 13.0% |
| GPT-4o | 45.9% | 30.9% |
| Gemini 2.5 Pro | 41.4% | 6.1% |

At 50K-token prompts: GPT-5.2 cuts cost from $0.253 to $0.029 (-89%); Sonnet 4.5 from $0.667 to $0.080 (-88%). At 500-token prompts (below the 1024-token minimum), every provider showed a 10-18% TTFT **regression**: caching pays off only above the minimum prefix.

<!-- src: audit-agentic-mcp/references/patterns/caching-economics.md#Case 6 — Claude Code TTL regression: $2,531 overpaid across two machines -->
### Case 6: Claude Code TTL regression, $2,531 overpaid across two machines

The vendor silently flipped Claude Code's default TTL from 1h to 5m around 2026-03-06. Across 119,866 calls on two machines: Sonnet 4.6 actual $5,561 against $4,612 on 1h (+$949, 17.1% waste); Opus 4.6 $9,269 against $7,687 (+$1,582). Total $2,531 overpaid in about 5 weeks. Takeaway: vendor-side TTL defaults are not stable; instrument the `cache_creation_input_tokens_5m` / `_1h` ratio (monitoring rule in `../mcp/budget-cache-ttl-and-monitoring.md`). Issue filed 2026-04-12 (anthropics/claude-code #46829); press coverage the next day.
