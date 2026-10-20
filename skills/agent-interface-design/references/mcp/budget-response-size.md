# Context budget: response size, tiered verbosity, terminal noise, delivery strategy

> Read when: tool responses are large or noisy, a session runs long, or you must pick between pagination, truncation and streaming.

Companion to `budget-tool-definitions.md`. Code: `../frameworks/mcp-python/context-engineering.md`, `../frameworks/mcp-ts/context-engineering.md`. Truncation signal wording: `responses-curated-and-semantic.md`.

<!-- src: audit-agentic-mcp/references/patterns/context-engineering.md#3. Shrink Tool Responses as Context Fills Up (Tiered Verbosity) -->
## Shrink responses as context fills up (tiered verbosity)

A tool that returns full pagination, rich metadata and verbose field names is fine early in a session when the window is mostly empty. The same payload near the end of a long session can push the model into truncation territory. Make verbosity a function of how much context remains.

Three tiers keyed to the remaining context fraction:
- **Above 70% remaining:** return everything: full records, all fields, pagination metadata.
- **Between 40% and 70%:** summary mode: a count, the top 5 items, and a `detail_available` flag with a hint to call `get_details(id)` ("Showing 5 of N. Call get_details(id) for full records.").
- **Below 40%:** only the count and a directive to narrow the query ("Context low. Narrow your query or call get_details(id) for a specific record.").

The remaining fraction is `max(0, 1 - session_tokens / total_window)`; thresholds `full` 0.70 and `summary` 0.40 (code: framework file). A tool that blindly returns 10,000 rows at turn 40 of a 50-turn session silently degrades model performance; a tiered response gives the model a graceful off-ramp.

<!-- src: audit-agentic-mcp/references/patterns/context-engineering.md#4. Strip ANSI Codes and Progress Bars Before Returning CLI Output -->
## Strip ANSI codes and progress bars from wrapped CLI output

Servers that wrap command-line tools inherit everything those tools emit: ANSI color codes, carriage-return progress bars, Unicode box-drawing characters, alignment padding built for terminals. None of it means anything to an LLM; it is pure token waste and it is significant. Measured reductions for common commands (docker build, git log, npm install, test runners, cargo build) range from 68% to 95% (table: `../fresh/mcp-token-benchmarks.md`); decoration can inflate output 5-95x in token terms.

Strip, in order:
- ANSI escapes for colors and cursor movement.
- ANSI screen/line erase sequences.
- Carriage-return redraw segments (`[^\n]*\r`).
- Spinner frame characters.
- Box-drawing characters.
- Runs of three or more newlines, collapsed to two; then trim.

Suppress at the source too: run the child with `NO_COLOR=1`, `TERM=dumb` and flags such as `--no-color`; merge stderr after stdout. Stripping is a zero-logic-change optimization that pays back immediately.

<!-- src: audit-agentic-mcp/references/patterns/context-engineering.md#5. Use the Right Data Delivery Strategy for Each Tool Type -->
## Pick the delivery strategy per tool type

| Strategy | Suits | Cost and quality profile |
|---|---|---|
| **Pagination** | Lists, database queries, anything likely to exceed 100 items | Per-page token cost is low and bounded; adds 2-3 extra turns; no data lost |
| **Truncation** | One-shot responses and logs where a quick look is enough | Hard token ceiling with zero latency overhead; quality degrades past about 5,000 items because the model never knows what was cut |
| **Streaming** | Live data and real-time log tailing | Each chunk is cheap and delivery is real-time; the model has an incomplete view until the stream closes |

Best in practice: hybrid first-page-plus-summary. A paginated response carries `results`, `total_results`, `page`, `total_pages`, `has_more`, and a `hint` only when `has_more` is true ("Showing N of M. Use page=2 for more."). Default page size is 20. Truncation helper: cut at a character cap (default 8000) and append "[...truncated — N chars omitted. Use a narrower query for more.]" so the model always knows what was cut.

Pagination without a summary forces extra turns; truncation without a signal causes silent data loss; the hybrid gives the model full agency over whether to pay for more.
