# Bounded server-side continuation for research loops

> Read when: a read-only research, search or discovery tool could spend a small internal planning budget to return the next step along with the results.

Code (TypeScript): `../frameworks/mcp-ts/agentic-patterns-continuation.md`. Response shape and steering rules: `responses-steering-and-examples.md`, `../decisions/steering-contract.md`.

<!-- src: audit-agentic-mcp/references/patterns/agentic-patterns.md#7. Bounded Server-Side Continuation for Research and SEO Loops -->
## Bounded server-side continuation

Sometimes the best tool does not stop at "here are the top 10 results". For open-ended research, search and SEO workflows the server can spend a **small internal planning budget** deciding what the next search wave should be.

This is an advanced pattern. Default MCP design still prefers explicit, transparent tool boundaries. But when the workflow is **read-only, repetitive and frontier-building**, a bounded internal planner can beat "return raw results and hope the agent figures out the next 12 queries". High-value use: research and SEO exploration where the first wave is only a starting point.

Worked example:
- Tool input: a seed keyword or topic.
- Wave 1: the server fetches the first result page and clusters the results.
- Internal planner turn: a second model call reads the results and identifies missing angles, weak source diversity, stale content or intent gaps.
- Tool output: current results plus `recommended_next_queries`, `coverage_gaps`, and optionally a few prefetched follow-up searches.

Input schema of the example tool `research_serp`: `query` (string), `continuation_mode` (enum `none`, `suggest`, `prefetch`; default `suggest`), `max_followups` (1-5, default 3), `max_results` (3-10, default 10). The output carries both `structuredContent` (seed query, `summary`, `results`, `coverage_gaps`, `recommended_next_queries`, `server_actions_taken`, `prefetched_results`, `budget_remaining` such as `followup_queries_remaining`, `stop_conditions`) and a text `content` copy of the essentials (see `responses-formats-and-structured.md`). Example stop conditions: "Stop if the next wave adds fewer than 2 novel high-quality domains." and "Stop if two consecutive waves target the same search intent with no new evidence."

Why it works:
1. The server collapses a repeated research loop into one bounded tool call.
2. The internal planner works on the server's own structured result set, not on lossy user re-prompts.
3. The agent gets current evidence **and** the next frontier, so it spends fewer turns rediscovering obvious follow-ups.

How to think about it:
- The job is not "return results"; it is "advance the search frontier".
- Steer by **gaps**, not just similarity: missing intent, freshness, authority, evidence type.
- Return recommendations as explicit objects with `query`, `reason` and expected signal, not a vague paragraph.
- Distinguish what the server **already did** from what the agent **should do next**.

Safe operating rules:
- Use it for **read-only** or low-risk internal work first.
- Bound it with hard caps: max waves, max follow-up searches, max spend, max wall-clock time.
- Emit `server_actions_taken`, `budget_remaining` and `stop_conditions` in every response.
- Never hide irreversible external actions behind an internal planner loop.
- Evaluate it with transcripts and offline tasks before calling it "better".

Use it for: research servers, SEO discovery tools, competitor and result-page exploration, domain mapping and taxonomy expansion.

Do not use it for: destructive workflows; audited workflows where every step must stay explicit in the agent transcript; cases where the internal planner would mostly guess instead of working from real evidence.

Related guidance: published vendor tool guidance generally favors clear tool boundaries, structured responses and fewer wasted round-trips. Treat internal planner turns as an advanced exception that must earn its keep with evaluations, not the default design.
