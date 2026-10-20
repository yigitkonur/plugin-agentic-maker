# Tool responses: curated, concise, semantic, truncation-aware

> Read when: you are shaping what an MCP tool returns: how much, which identifiers, and what to say when results are cut off.

<!-- src: audit-agentic-mcp/references/patterns/tool-responses.md#Tool Response Patterns -->
Craft responses that steer the model toward correct next steps, minimize token waste, and serve both the user and the agent. Next-step hints and example responses: `responses-steering-and-examples.md`. Output formats and structured content: `responses-formats-and-structured.md`. Code: `../frameworks/mcp-python/tool-responses.md`.

<!-- src: audit-agentic-mcp/references/patterns/tool-responses.md#Pattern 1: Treat Every Tool Response as a Prompt to the Model -->
## Treat every response as a prompt

This is the single most important MCP design insight: stop treating MCP servers like APIs with better descriptions. Every response is injected into the model's context and becomes part of its reasoning input. A model starts each conversation with only tool descriptions; once it starts calling tools, responses become the primary steering mechanism.

A raw API response: `{"members": [{"id": "u1", "name": "Jane"}, {"id": "u2", "name": "Bob"}], "total": 25}`.

An MCP-optimized response:

```json
{
  "members": [{"name": "Jane Doe", "activity_score": 92}, {"name": "Bob Smith", "activity_score": 45}],
  "total": 25,
  "summary": "Found 25 active members in the last 30 days. Top contributor: Jane Doe.",
  "next_steps": "Use bulkMessage() to contact these members, or filter by activity_score to focus on top contributors."
}
```

Include:
- A human-readable summary of the result.
- Suggested next actions with specific tool names.
- Context that helps the model interpret the data.
- Pagination hints when results are truncated.

Avoid:
- Raw JSON dumps with no context.
- Internal IDs without human-readable labels.
- Technical metadata the model cannot reason about.

Next-step text is steering; the tension with untrusted tool output is stated once in `../decisions/steering-contract.md`.

<!-- src: audit-agentic-mcp/references/patterns/tool-responses.md#Pattern 2: Add a Response Format Enum to Every Data-Returning Tool -->
## Add a concise/detailed response-format parameter

Give the agent control over verbosity with a `response_format` parameter (enum `detailed`, `concise`; default `concise`). This single pattern can cut token usage by 60-70% (measured figures: `../fresh/mcp-token-benchmarks.md`).

- **Concise** (default): for browsing, scanning, initial discovery. Example fields: `name`, `email`, `summary`.
- **Detailed**: when the agent needs IDs or metadata for follow-up calls. Example adds `recent_transactions`, `notes`, `internal_id`, and a `thread_ts` "for downstream tool calls".

This avoids two separate tools for the same data and keeps the tool count low. Over a multi-step workflow with 10+ calls the savings compound. Choosing between formats on the wire: `../decisions/response-format.md`.

<!-- src: audit-agentic-mcp/references/patterns/tool-responses.md#Pattern 3: Return Semantic Identifiers, Not Opaque UUIDs -->
## Return semantic identifiers, not opaque UUIDs

Models reason in natural language. A bare `"id": "550e8400-e29b-41d4-a716-446655440000"` cannot be reasoned about, is not remembered across calls, and is likely to be hallucinated when passed to the next tool.

Bad:

```json
{"project_id": "550e8400-e29b-41d4-a716-446655440000",
 "channel_id": "C04BKGH3L8P",
 "image_url": "https://cdn.example.com/avatars/256px/a7b3c9d1.jpg"}
```

Good:

```json
{"project_name": "Q4 Marketing Campaign",
 "project_id": "q4-marketing",
 "channel_name": "#general",
 "profile_image": "Jane's avatar (square, professional headshot)"}
```

Practical approach:
- Always include a human-readable name alongside any ID.
- Use slug-style IDs when possible (`q4-marketing` rather than a UUID).
- Translate internal codes to descriptive labels.
- If you must return UUIDs, pair them: `"project": {"id": "550e...", "name": "Q4 Marketing"}`.
- For images, describe them in text rather than returning raw pixel-dimension URLs.

When a later call needs an ID, the model is more likely to pass the right one if it can associate it with a meaningful name.

<!-- src: audit-agentic-mcp/references/patterns/tool-responses.md#Pattern 4: Prepend Truncation Guidance When Results Are Cut Off -->
## Prepend truncation guidance when results are cut off

When you paginate or truncate, never return partial data silently. Tell the model what happened and how to get more. Example: fetch `limit + 1` rows to detect truncation; return `results`, `count`, `total_available`, and, when truncated, a `guidance` string: "Showing 50 of N results. Consider filtering by date range (e.g., start_date='2025-01-01') or adding more specific terms to narrow results."

Key details:
- Place the guidance **before** the data so the model reads it first.
- Suggest specific parameter values that would shrink the result set.
- Include the total count so the model can decide whether narrowing is worthwhile.
- Plan for client-side response-size caps (reported cap: `../fresh/mcp-client-and-sdk-quirks.md`).

Anti-pattern: silently returning the first N results with no sign that more exist. The model assumes the data is complete and draws wrong conclusions. Delivery strategies: `budget-response-size.md`.
