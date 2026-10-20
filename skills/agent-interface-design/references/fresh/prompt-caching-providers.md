---
as_of: 2026-04-14
verify_before_citing: true
---
# Prompt-caching mechanics per provider

> Read when: you need minimum prefix sizes, TTLs, write premiums, read discounts, breakpoint limits or invalidators for a provider's prompt cache; verify before citing.

Column dates are each provider page's own (Anthropic 2026-04, OpenAI 2026-04, Gemini API 2026-03, Vertex AI 2026-04, Bedrock 2026-01); the pages were pulled 2026-04-14. Rules that use these facts: `../mcp/budget-cache-stable-prefix.md`, `../mcp/budget-cache-ttl-and-monitoring.md`. Cost math: `prompt-caching-cost-math.md`. Links: `prompt-caching-sources.md`.

<!-- src: audit-agentic-mcp/references/patterns/caching-economics.md#Per-Provider Mechanics Reference -->
## Per-provider mechanics

The first decision is which cache surface you optimize against. Minimums, TTLs, write premiums and invalidation triggers differ materially across vendors.

| Dimension | Anthropic (docs.claude.com, 2026-04) | OpenAI (developers.openai.com, 2026-04) | Gemini API (ai.google.dev, 2026-03) | Vertex AI (cloud.google.com, 2026-04) | Bedrock (aws.amazon.com, 2026-01) |
|---|---|---|---|---|---|
| **Min prefix** | 1024 tok (Sonnet 4/4.5/3.7, Opus 4/4.1); 2048 tok (Sonnet 4.6, Haiku 3/3.5); 4096 tok (Opus 4.5/4.6, Haiku 4.5) | 1024 tok; cache hits accrue in 128-tok increments | 1024 tok (2.5 Flash, 3 Flash); 2048 tok (2.5 Pro implicit); 4096 tok (3 Pro Preview) | 2048 tok (2.0/2.5); 4096 tok (Gemini 3/3.1) | Inherits Anthropic mins for Claude models |
| **TTL options** | 5 min default (auto-refreshed on hit); 1 hour extended | In-memory 5-10 min inactivity (up to 1h); `prompt_cache_retention: "24h"` on gpt-5.x and gpt-4.1 | Default 1h; any custom TTL ≥ 1 min | ≥ 1 min, no upper bound for explicit caches; implicit deleted within 24h | 5 min default; 1 hour GA 2026-01-26 for Sonnet 4.5 / Haiku 4.5 / Opus 4.5 |
| **Write multiplier** | 5m: 1.25× input; 1h: 2.0× input | **No write premium** | Implicit: free. Explicit: standard input rate + hourly storage | Implicit: free; explicit: standard + per-minute storage | Same as Anthropic |
| **Read discount** | 0.1× (90% off) | ~0.5× on legacy GPT-4o / o-series; 0.1× (90%) on GPT-5.x per openai.com pricing 2026-04 | 2.5+: 0.1× (90%); 2.0: 0.25× (75%) | Matches Gemini API tier | Same as Anthropic |
| **Breakpoint limit** | Max 4 per request, `cache_control: {type:"ephemeral"}`; canonical prefix order `tools → system → messages`; 20-block lookback | Implicit; route hash derived from first ~256 tokens | Implicit + explicit `cachedContent` name; no hard block limit | Same as Gemini API | Inherits Anthropic |
| **Storage fee** | None | None | **$4.50 / 1M tok / hour** (2.5 Pro ≤200K); **$1.00 / 1M tok / hour** (2.5 Flash) | Hourly, prorated by minute for explicit caches; 0 for implicit | None |
| **Primary invalidators** | Tool-def change (name/desc/params); toggling `web_search`, `citations`, or `speed:"fast"`; adding/removing images; `tool_choice` change (messages only); extended-thinking setting change; any byte change at or before a breakpoint | Prefix change; tool list change; image/detail change; model or version change; inactivity; spillover above ~15 rpm at a single `prompt_cache_key` | Anything beyond `ttl` / `expire_time` updates is unsupported; implicit caches also require identical prefix + temporal locality | Same as Gemini API | Same as Anthropic |

Anthropic's 1h write premium (+100%) is 4x its 5m premium (+25%); an "8x" figure would be an arithmetic error (100% divided by 25% is 4).
