---
as_of: 2026-04-14
verify_before_citing: true
---
# Prompt-caching cost worksheet and break-even

> Read when: you need to estimate what caching saves for a 20-tool MCP agent session, or how many cache reads a write premium needs to pay off; verify the prices before citing.

Prices are those of April 2026 and will move. Provider mechanics: `prompt-caching-providers.md`. Rules: `../mcp/budget-cache-ttl-and-monitoring.md`.

<!-- src: audit-agentic-mcp/references/patterns/caching-economics.md#Cost Math Worksheet — 20-Tool MCP Server, 10-Turn Agent Session -->
## Cost worksheet: 20-tool MCP server, 10-turn agent session

Reference workload: 20 MCP tools in the stable tool block, 10 agentic turns inside one TTL window, a 30K-token prefix (system prompt + tool definitions + shared CLAUDE.md), 2K output per turn, and a tail user+assistant suffix that grows about 1.5K per turn to about 12K by turn 10.

<!-- src: audit-agentic-mcp/references/patterns/caching-economics.md#Turn-1 cache-miss row (one-off cost of seeding the cache) -->
### Turn-1 cache-miss row (one-off cost of seeding the cache)

| Provider / Model | Prefix cost | Cache-write premium | Output cost | Turn-1 total |
|---|---|---|---|---|
| Claude Sonnet 4.6 — 5m TTL | 30K × $3/M = $0.0900 | +25% of prefix = $0.0225 | 2K × $15/M = $0.0300 | **$0.143** |
| Claude Sonnet 4.6 — 1h TTL | $0.0900 | +100% = $0.0900 | $0.0300 | **$0.210** |
| Claude Opus 4.6 — 5m TTL | 30K × $5/M = $0.1500 | +$0.0375 | 2K × $25/M = $0.0500 | **$0.238** |
| GPT-5.4 (auto-cache) | 30K × $2.50/M = $0.0750 | $0 | 2K × $15/M = $0.0300 | **$0.105** |
| Gemini 2.5 Pro — explicit 1h | 30K × $1.25/M = $0.0375 | $0 (storage tracked separately) | 2K × $10/M = $0.0200 | **$0.058** + storage |

<!-- src: audit-agentic-mcp/references/patterns/caching-economics.md#Full 10-turn session totals (all cache hits inside one TTL window) -->
### Full 10-turn session totals (all cache hits inside one TTL window)

| Strategy | 10-turn total | Savings vs. no cache |
|---|---|---|
| Sonnet 4.6, no cache | ~$1.43 | baseline |
| **Sonnet 4.6, 5m cache** | **$0.575** | **−60%** |
| Sonnet 4.6, 1h cache | $0.642 | −55% |
| Opus 4.6, no cache | ~$2.30 | baseline |
| Opus 4.6, 5m cache | $0.958 | −58% |
| GPT-5.4, no cache | ~$1.15 | baseline |
| GPT-5.4, auto-cache | $0.510 | −56% |
| Gemini 2.5 Pro, no cache | ~$0.63 | baseline |
| Gemini 2.5 Pro, explicit 1h | $0.440 | −30% (storage dominates at 30K) |
| Gemini 2.5 Flash, explicit 1h | $0.087 | −50% |

The storage drag on Gemini 2.5 Pro at this prefix size is why explicit caching only pays off once the prefix is at least 100K tokens or the reuse rate is high (rule: TTL section of `../mcp/budget-cache-ttl-and-monitoring.md`).

Arithmetic check: the turn-1 rows, the percentages in the totals table and the break-even figures below recompute from the numbers given. The 10-turn totals were not re-derived because the page does not say how the growing tail is priced.

<!-- src: audit-agentic-mcp/references/patterns/caching-economics.md#Break-Even Analysis — How Many Reads Before a Write Pays Off -->
## Break-even: how many reads before a write pays off

For multiplier-style pricing the formula is `N = (M − 1) / (1 − R)`, where `M` is the write multiplier (against the base input rate) and `R` is the read multiplier. `N` is the number of cache reads needed before the writer recoups the premium.

| Provider / TTL | M | R | Reads to break even |
|---|---|---|---|
| Anthropic 5m | 1.25 | 0.10 | 0.28 → pays off after **1 hit** |
| Anthropic 1h | 2.00 | 0.10 | 1.11 → pays off after **2 hits** (Anthropic docs state this exactly) |
| OpenAI auto-cache | 1.00 | 0.10 | 0 → **always a win** at ≥ 1024 tok |
| Gemini 2.5 implicit | 1.00 | 0.10 | 0 → **always a win** |
| Gemini 2.5 Pro explicit 1h (30K prefix) | 1.00 + storage | 0.10 | Storage dominates. 30K × $4.50/M/hr = $0.135/hr storage; each hit saves ~$0.0338. Break-even ≈ **4 hits/hour** |

Source for the table: an analysis dated 2026-02-17, the Anthropic pricing docs and the Gemini pricing page (2026-04-14).

Practitioner reality check (an Anthropic engineer quoted by The Register, 2026-04-13): "Prompt cache misses when using the 1M-token context window are expensive. If you leave your computer for over an hour and then continue a stale session, it's often a full cache miss."
