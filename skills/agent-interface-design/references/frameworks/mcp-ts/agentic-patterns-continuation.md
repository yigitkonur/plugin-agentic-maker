# Bounded Server-Side Continuation in TypeScript

> Read when: you are building a read-only research tool that returns the next-query frontier and discloses its internal planner turn, in TypeScript.

Explanation and rules: ../../mcp/patterns-bounded-continuation.md

## Pattern 7: Bounded Server-Side Continuation for Research and SEO Loops

```typescript
server.tool("research_serp", "Search the web for a topic and return the current frontier for deeper research or SEO expansion.", {
  query: z.string(),
  continuation_mode: z.enum(["none", "suggest", "prefetch"]).default("suggest"),
  max_followups: z.number().min(1).max(5).default(3),
  max_results: z.number().min(3).max(10).default(10),
}, async ({ query, continuation_mode, max_followups, max_results }) => {
  const serp = await searchWeb(query, max_results);

  const planner = await internalModel.planNextSearchWave({
    seedQuery: query,
    currentResults: serp,
    goals: [
      "find missing search intents",
      "increase source diversity",
      "identify the highest-signal next queries",
    ],
    maxQueries: max_followups,
  });

  const prefetched =
    continuation_mode === "prefetch"
      ? await Promise.all(planner.recommended_queries.map((item) => searchWeb(item.query, 5)))
      : [];

  return {
    structuredContent: {
      seed_query: query,
      summary: planner.summary,
      results: serp,
      coverage_gaps: planner.coverage_gaps,
      recommended_next_queries: planner.recommended_queries,
      server_actions_taken: [
        {
          type: "internal_planner_turn",
          purpose: "derive the next search frontier from current SERP",
        },
        ...(continuation_mode === "prefetch"
          ? [{ type: "prefetch_followup_searches", count: prefetched.length }]
          : []),
      ],
      prefetched_results: prefetched,
      budget_remaining: {
        followup_queries_remaining: Math.max(0, 5 - max_followups),
      },
      stop_conditions: [
        "Stop if the next wave adds fewer than 2 novel high-quality domains.",
        "Stop if two consecutive waves target the same search intent with no new evidence.",
      ],
    },
    content: [{
      type: "text",
      text: JSON.stringify({
        seed_query: query,
        summary: planner.summary,
        recommended_next_queries: planner.recommended_queries,
        stop_conditions: [
          "Stop if the next wave adds fewer than 2 novel high-quality domains.",
          "Stop if two consecutive waves target the same search intent with no new evidence.",
        ],
      }, null, 2),
    }],
  };
});
```
