# Learn from successful calls and compact conversations by priority

> Read when: tool calls keep failing on a complex API and you want error responses to carry a working example, or a long MCP session is overflowing the context window.

<!-- src: audit-agentic-mcp/references/patterns/session-and-state.md#1. Log Successful Tool Calls to Build a Learning Database -->
## Log successful calls and quote one in the next error

When the server wraps a complex API, record every successful tool call and its parameters. When a later call fails, look up a similar successful call and append its parameters to the error response ("A similar successful call used these parameters: ... Try adjusting your parameters to match this pattern."), returned with `isError: true`. One practitioner reported this cut API call errors by more than 50%; the model learns from its own and other sessions' successful patterns.

Implementation details:
- Store in a simple JSONL file or SQLite database; each record has `endpoint`, `params`, `timestamp`.
- Index by endpoint and key parameter patterns.
- Include timestamps to weight recent successes higher.
- Consider embedding-based similarity for fuzzy matching.

Privacy: be careful about logging sensitive parameters. Strip PII before storing. Code: [python](../frameworks/mcp-python/session-and-state.md).

<!-- src: audit-agentic-mcp/references/patterns/session-and-state.md#5. Conversation Compaction Priorities -->
## Compact by priority, not by age

Long MCP sessions accumulate messages until they overflow the context window. Naive truncation (drop oldest) loses critical schema context. Use priority-aware compaction.

| Priority | What it is | Policy |
|---|---|---|
| Anchor | Schema definitions, structural | Always keep |
| Important | Substantial query results, data | Keep |
| Contextual | Useful background, explanations | Summarize if full |
| Routine | Ordinary dialogue, confirmations | May drop |
| Transient | Acks, "ok", status pings | Drop first |

Compact bottom-up: drop Transient, then Routine, then summarize Contextual. Anchor and Important survive until the session ends.

Cache the compaction by a SHA-256 content hash of the joined message contents (stored with a 3600 s TTL) so repeated compaction of the same history is an O(1) lookup. Classify messages at creation time, not at compaction time: schema or tool-definition messages are anchor; a tool result longer than 500 characters is important; other tool results are contextual; an assistant message shorter than 20 characters is transient; everything else is routine. Classify upfront, compact bottom-up, cache results for O(1) reuse. Classifier and cache code: [typescript](../frameworks/mcp-ts/session-and-state.md).

Source: pgEdge (lessons from writing an MCP server for PostgreSQL).
