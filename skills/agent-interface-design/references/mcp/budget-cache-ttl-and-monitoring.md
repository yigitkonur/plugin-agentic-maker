# Prompt caching: TTL choice, breakpoint budget, tool results, monitoring, stacking

> Read when: the prefix is already stable and you must choose TTLs, allocate breakpoints, handle repeated tool results, or detect that a vendor default changed.

Companion to `budget-cache-stable-prefix.md`. Numbers (write premiums, TTLs, break-even tables, case studies) are dated and live in `../fresh/prompt-caching-providers.md`, `../fresh/prompt-caching-cost-math.md` and `../fresh/prompt-caching-cases.md`; this file keeps the rules.

<!-- src: audit-agentic-mcp/references/patterns/caching-economics.md#Pattern 4: Match TTL to Content Lifetime, Not Convenience -->
## Match TTL to content lifetime, not convenience

The short TTL is cheap to write; the long TTL costs more to write. Some vendors charge no write premium and bill hourly storage instead. Choosing the right TTL per block matters more than choosing one TTL overall.

> Reconciled: the source said the 1h write premium is "8x" the 5m one while giving +25% (5m) and +100% (1h) in the same file. 100 / 25 is 4, so this file uses 4x. Figures: `../fresh/prompt-caching-providers.md`.

Do:
- Use the **long TTL (1h)** only for genuinely static content: system prompt, tool block, shared project context. These rarely change within an hour.
- Use the **short TTL (5m)** for the sliding conversation window. Agent loops usually tick in seconds.
- Respect the breakpoint cap: BP1 on the last static tool (1h), BP2 on the last turn of prior conversation (5m). Do not stack more than you need.
- For explicit caches that bill storage (the source's example: a large-context Gemini model), enable only when the prefix is at least 100K tokens **or** the hit rate exceeds 4 per hour per the break-even table.

Don't:
- Put the conversation history on the long TTL: you pay the 2x premium on a block that rewrites every 2-3 minutes.
- Assume the vendor's default TTL is stable; monitor the ratio (see the monitoring section below).

<!-- src: audit-agentic-mcp/references/patterns/caching-economics.md#Pattern 7: Treat Tool Results as a Separate Cache Problem -->
## Treat tool results as a separate cache problem

Prompt caching saves on the fixed prefix (30K tokens in the worked example). It does not dedup repeated tool results across turns: the model still spends input tokens re-reading the same repository file each time it asks.

Do:
- Return stable URIs via MCP Resources so the client can dedup across turns. A resource reference is a few tokens; the resolved content lives outside the prompt window on clients that support it.
- Pair a Redis / Durable Object / in-memory result cache keyed by `hash(tool_name + sorted(args))` (L1/L2/L3 layering belongs to session-and-state design).
- For idempotent read tools (file read, search, metadata fetch), add a `cache_ttl` hint to the response so the client knows when reuse is safe.

Don't:
- Conflate provider prompt caching with application response caching. Both matter; neither substitutes for the other.
- Ignore the tail: even with 90% off on the prefix, 10 turns of fat tool results can still dominate the bill. Response size: `budget-response-size.md`.

<!-- src: audit-agentic-mcp/references/patterns/caching-economics.md#Pattern 8: Budget the 4-Breakpoint Cap Across Features, Not Data Types -->
## Budget the breakpoint cap across features, not data types

A provider that caps breakpoints per request (4 for the source's vendor; see the providers file) makes every feature compete for the same slots: system prompt, parallel tool bundles, conversation chunks, extended-thinking blocks.

Do:
- Plan the 4 slots as a feature-level budget. Typical allocation: BP1 system + tools (1h), BP2 prior conversation (5m), BP3 reserved for the parallel tool-call bundle, BP4 held for extended-thinking continuity.
- If extended thinking is on and you pass non-tool results during thinking, the API strips all previously cached thinking blocks. Keep non-tool content out of thinking turns.
- Drop breakpoints you do not actively save on; an unused `cache_control` still counts against the 4.

Don't:
- Let the SDK sprinkle breakpoints automatically. Make placement explicit.
- Enable extended thinking and parallel tool use together without measuring; they fight for the cap.

<!-- src: audit-agentic-mcp/references/patterns/caching-economics.md#Pattern 10: Monitor Cache Creation Ratios — Vendor Defaults Drift -->
## Monitor cache-creation ratios; vendor defaults drift

The usage response exposes cache writes split by TTL in a nested object (`cache_creation.ephemeral_5m_input_tokens`, `cache_creation.ephemeral_1h_input_tokens`; `cache_creation_input_tokens` is their sum) and reads in `cache_read_input_tokens`. Their ratio is the single most useful signal that something changed upstream.

Do:
- Log both counters per request, with `cache_read_input_tokens`.
- Compute a rolling 7-day ratio of 1h-writes to 5m-writes, grouped by model. Alert when the ratio drops by more than 30% against the trailing baseline.
- Show the ratio on an internal dashboard next to per-model cost.
- Re-run the break-even math after any alert and confirm the route still wins.

Don't:
- Trust that your SDK default TTL is the vendor default TTL.
- Assume a cost anomaly is your fault before checking the vendor's recent changelog.

Case evidence (a silent default-TTL flip and its cost): `../fresh/prompt-caching-cases.md`.

<!-- src: audit-agentic-mcp/references/patterns/caching-economics.md#Pattern 11: Pair Prompt Caching With Batch and Code-Execution for Compounding Wins -->
## Pair caching with batch and code execution

Prompt caching multiplies with other cost levers; it is not an alternative to them. The largest documented savings stack at least two strategies on top of caching.

Do:
- Compose caching with the vendor's message-batch API (caching discounts apply to batch requests).
- Compose caching with the code-execution pattern (`budget-tool-definitions.md`): the model uses `execute_code` to navigate tool indices without expanding the cached tool block.
- Compose caching with response-level caching: the prompt cache cuts prefix cost, the response cache removes duplicate tool round-trips entirely.

Don't:
- Treat caching as a silver bullet. Very-large-context coding sessions stay expensive on the first turn whatever you do; only batch + cache + code execution together keep long tasks affordable.

> Reconciled: the source's TTL pattern pointed to "Pattern 11" for monitoring; monitoring is Pattern 10, so the pointer above names the monitoring section here. Its other cross-references (to a sibling context file section 2) now point to `budget-tool-definitions.md`.
