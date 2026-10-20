---
as_of: 2026-04-14
verify_before_citing: true
---

# Model rules for response size, context windows, history pruning, and retries

> Read when: you set a per-tool response cap, target short-context models, prune tool-call history, or decide who owns retries. Rules 7, 8, 9, 12 of the adjustment rules.

Code (response cap): `frameworks/mcp-model-portability-snippets.md`. Index of the other rules: `model-behavior-rules-tool-surface.md`. Core budget guidance: `mcp/budget-*`.

<!-- src: audit-agentic-mcp/references/patterns/model-behavior.md#Pattern 7: Cap individual tool responses at ≤25,000 tokens; trim chatty tools to ≤1,000 -->
## Rule 7: Cap individual tool responses at 25,000 tokens; trim chatty tools to 1,000

Microsoft Research (Sep 2025) measured a 1,312-tool corpus: the top tool averaged 557,766 tokens per response and 16 tools exceeded 128,000 tokens. Anthropic's default Claude Code limit is 25,000 tokens per tool response, and studies cited by Klavis show overly long responses costing up to 91% of performance in worst cases. Hard-cap response size, paginate built in, default to small, and expose a `more` or `page` tool for deeper fetches.

Reference shape: `MAX_TOKENS = 25_000` (matches the Claude Code default), `DEFAULT_PAGE_SIZE = 50`; if the rendered page exceeds the cap, halve the rows; return `page`, `rows`, `has_more`, and a `next_step` hint ("Call list_records(page=N+1) for more").

Source: Microsoft Research 2025-09-11 tool-space interference study; Klavis AI 2025-10-25.

<!-- src: audit-agentic-mcp/references/patterns/model-behavior.md#Pattern 8: Size tool-response caps against the actual context window of the target model -->
## Rule 8: Size tool-response caps against the context window of the target model

The same 1,312-tool corpus, projected across 6-10 tool-call sessions, produced:

- 25 overflows against GPT-5's 400K window,
- 40 overflows against GPT-4o's 128K window,
- 90 overflows against Qwen3's 32K window,
- 109 overflows against Phi-4's 16K window.

Short-context open-weight models (Qwen3 32K, Phi-4 16K, older Llama variants) are unusable as MCP hosts without tighter per-tool caps than the 25K default. If your target includes short-context hosts, cap individual tool responses at 5,000 tokens or fewer and document it as a deployment constraint.

Source: Microsoft Research 2025-09-11, as summarized by Klavis AI 2025-10-25.

<!-- src: audit-agentic-mcp/references/patterns/model-behavior.md#Pattern 9: Compact or prune tool-call history past ~50K input tokens -->
## Rule 9: Compact or prune tool-call history past about 50K input tokens

Chroma's 2025 "Context Rot" study found all frontier models show monotone context-length degradation: LongMemEval focused prompts (about 300 tokens) significantly outperform full prompts (about 113K tokens), and the Repeated-Words stress test shows consistent degradation as input grows. MCP sessions that accumulate tool-response history without trimming hit this wall predictably.

For an MCP host:

- After about 50K input tokens, summarize older tool results into a "history_summary" tool block and drop raw content.
- Keep the last N tool results raw (N=3 is a reasonable default) for local coherence.
- For Claude, put the stable summary behind a cache breakpoint.

Source: Chroma 2025 Context Rot study.

<!-- src: audit-agentic-mcp/references/patterns/model-behavior.md#Pattern 12: Prefer built-in retry with explicit tool-call budget over model-driven retries -->
## Rule 12: Prefer built-in retry with an explicit tool-call budget over model-driven retries

Models do not self-limit well when a tool returns an error: they retry with the same arguments, or invent new arguments that escalate damage. Implement a server-side retry/backoff policy on transient failures and return a terminal `isError: true` with clear guidance after N attempts, so the model does not keep calling. Pair with `mcp/errors-*` and `decisions/error-strategy.md` for error-shape details.
