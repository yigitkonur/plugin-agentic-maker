# Prompt caching: keep the prefix byte-stable

> Read when: you want provider-side prompt caching to pay off for an MCP agent and must decide what may sit in the cached prefix and what may change.

<!-- src: audit-agentic-mcp/references/patterns/caching-economics.md#Prompt Caching and MCP Cost Economics -->
Provider-side prompt caching can drive per-turn MCP cost down 55-92% once the prefix stays byte-identical; the hard part is keeping it so across tool edits, reconnects and dynamic system prompts. This file covers prefix stability; TTL choice, tool results, monitoring and stacking are in `budget-cache-ttl-and-monitoring.md`.

Scope: the **provider** cache (what each vendor charges, what invalidates it). Tool-definition budgets: `budget-tool-definitions.md`; response size: `budget-response-size.md`; application-level response caching (L1/L2/L3, Redis, ETag) belongs to session-and-state design; why dynamic tool lists invalidate the cache: `patterns-dynamic-tool-lists.md`. Prices, TTLs, minimum prefixes and the cost math: `../fresh/prompt-caching-providers.md`, `../fresh/prompt-caching-cost-math.md`. Before cache-sensitive changes run `agentic-maker probe mcp --budget`, and re-run after, so the audit can state the direction of change.

<!-- src: audit-agentic-mcp/references/patterns/caching-economics.md#Pattern 1: Freeze Tool Descriptions Before You Enable Caching -->
## Freeze tool descriptions before enabling caching

Any change to a tool name, description, JSON schema or parameter list invalidates the cache for the whole block containing it. Tool definitions sit at the front of the canonical prefix (`tools -> system -> messages`), so one edit cascades forward and invalidates every block after it.

Do:
- Version MCP tool surfaces in the repo (for example `schema_version: 3` in server metadata) and freeze that version before the caching campaign.
- Audit every PR that touches tool files like a critical-path code change, with a release-note entry.
- Ship schema changes as a coordinated roll: bump the version, rotate all callers, accept the one-time cache wipe.

Don't:
- A/B test tool descriptions in production by flipping the field per request.
- Normalize whitespace, re-order schema keys or auto-format tool definitions on startup; deterministic serialization is a correctness requirement once caching is on.
- Regenerate schemas from Pydantic/Zod models at request time with a non-deterministic generator.

Case evidence: `../fresh/prompt-caching-cases.md`.

<!-- src: audit-agentic-mcp/references/patterns/caching-economics.md#Pattern 2: Put Stable Content Before the Breakpoint, Volatile After -->
## Put stable content before the breakpoint, volatile content after

With explicit breakpoints, everything you want cached must sit at or before your last breakpoint, everything volatile after it. The canonical order is `tools -> system -> messages` (breakpoint cap and lookback window: `../fresh/prompt-caching-providers.md`).

Target order for an MCP agent:
1. System prompt (stable persona and product rules).
2. Tool block: static tools first, dynamic/subagent tools last.
3. Shared project context (CLAUDE.md / AGENTS.md / repo conventions).
4. [BREAKPOINT 1]
5. Conversation history older than the current turn.
6. [BREAKPOINT 2, sliding window]
7. Current user query and any just-fetched tool results.

Do:
- Put the `cache_control` marker on the last static tool, not the first.
- Keep current tool results out of the prefix; they belong after the last breakpoint.
- Log prefix bytes per turn and alert if the running SHA of the first 30K tokens changes for non-release reasons.

Don't:
- Put "current date", request IDs or user identifiers inside the system prompt block.
- Inline the latest retrieval chunk inside the cached prefix; it forces a fresh write every turn.

Case evidence: same file.

<!-- src: audit-agentic-mcp/references/patterns/caching-economics.md#Pattern 3: Never Renegotiate the MCP Tool List Mid-Session -->
## Never renegotiate the MCP tool list mid-session

Adding, removing or re-ordering one tool rewrites the whole tools block and forces a fresh cache write for the whole conversation. (`patterns-dynamic-tool-lists.md` states it in a sentence; this is the cost consequence.)

Do:
- Register every tool at session start. For feature-flagged tools register thin stubs with `defer_loading: true` (see the stub section below).
- Use a stable alphabetical or topological sort so re-registration yields byte-identical output.
- If a tool must be hidden mid-session, suppress it at the **routing layer**, not by unregistering.

Don't:
- Lazily attach MCP servers based on user intent detected at turn 3; that detonates the cache of turns 1-2.
- Assume "removing one unused tool" is free; it shifts the byte offset of every subsequent tool.

One widely used coding agent forbids post-session tool registration for exactly this reason (cases file).

<!-- src: audit-agentic-mcp/references/patterns/caching-economics.md#Pattern 5: Eliminate Every Byte-Varying Element From the Cacheable Prefix -->
## Eliminate every byte-varying element from the cacheable prefix

Silent invalidators kill more cache than explicit API changes. Top offenders: datetime strings, request IDs, user IDs and non-deterministic schema serialization.

Do:
- Freeze the current date **once per task** and format it `YYYY-MM-DD`, not ISO 8601 with seconds.
- Render system prompts from templates with stable placeholders; if the template interpolates the user's name inside the prefix, move the name into the first user message.
- Canonicalize CLAUDE.md / AGENTS.md / tool lists in a deterministic order at the server boundary (sort keys, strip trailing whitespace).
- Put per-user context in the tail message, not the cached prefix.

Don't:
- Include build SHA, deploy timestamp or server hostname in the system prompt.
- Let the agent's own "Current time: ..." preamble land before the breakpoint.
- Trust `JSON.stringify` key ordering: older V8 and Python dict iteration differ between runs.

A published case lists "freezing datetime to date-only" among five changes that lifted its hit rate from 7% to 84% (`../fresh/prompt-caching-cases.md`).

<!-- src: audit-agentic-mcp/references/patterns/caching-economics.md#Pattern 6: Pin One Provider Route Per Session -->
## Pin one provider route per session

Caches are per model **and** per provider region. Switching from the vendor's direct API to a cloud marketplace mid-session, even for the same model, gives a guaranteed 0% hit rate on the new route.

Do:
- Route all traffic of a session to one provider, one region, one model ID.
- Reserve alternate routes (cloud marketplaces, fallback regions) strictly for outage failover.
- For multi-region latency, shard users by region at signup, not per request.
- Treat "switch to a cheaper model" as a cache wipe; do it at session boundaries only.

Don't:
- Load-balance round-robin across routes; you pay the short-TTL write premium on every flip.
- A/B test model versions within a session.

<!-- src: audit-agentic-mcp/references/patterns/caching-economics.md#Pattern 9: Ship Thin Tool Stubs by Default, Hydrate Schemas on Demand -->
## Ship thin tool stubs, hydrate schemas on demand

With 20+ MCP tools the tool block alone can be 3-10K tokens. A thin stub first, full schema on demand, keeps the cached prefix small **and** byte-stable, as long as hydration happens through a message, not a tool edit.

Do:
- Register stubs such as `{"name":"mcp__slack__read_channel","description":"Read messages from Slack","defer_loading":true}`: a few tokens each.
- Append the full JSON schema as a **user or assistant message** when the model asks. Messages sit after the breakpoint and do not invalidate the cache.
- Combine with the code-execution discovery in `budget-tool-definitions.md`: the model finds schemas through code, not tool re-registration.

Don't:
- Load the schema back into the tool block after the model asks; that rewrites the prefix.
- Leave hydrated schemas in context after the call; they inflate the tail. Let the model discard them.

A coding agent's deferred-loading strategy is the canonical reference (cases file).
