# MCP errors: retry limits, framing, long tail, normalized inputs

> Read when: you are deciding how an MCP error should be worded, how many retries to allow, and what to echo back so the agent converges.

Companion to `errors-protocol-vs-tool.md`. Code: `../frameworks/mcp-python/error-handling.md`, `../frameworks/mcp-python/error-handling-recovery.md`.

<!-- src: audit-agentic-mcp/references/patterns/error-handling.md#Pattern 4: Include Retry Limits and Fallback Instructions in Errors -->
## Include retry limits and a fallback in the error

Unbounded guidance ("try again") can trap the model in an infinite loop. Always include a limit and a fallback.

```json
{"content": [{"type": "text",
  "text": "An unknown error occurred while processing the payment. Retry now. After three consecutive failures, provide the user a link to https://dashboard.example.com/manual-payment to complete the payment manually."}],
 "isError": true}
```

Implementation: pass a retry counter (`_retry_count`, starting at 0). On a transient failure below the limit, answer "Payment processing temporarily failed (attempt 1/3). Call process_payment(order_id='...', _retry_count=1) to retry." At `_retry_count >= 2`, answer "Payment processing failed after 3 attempts for order '...'. Ask the user to complete payment manually at: <link>". Without limits some models retry 10+ times, burning tokens and time; the fallback gives a human escalation path so the model does not give up entirely. A server-side limit that does not depend on the model: `errors-loop-breaker.md`.

<!-- src: audit-agentic-mcp/references/patterns/error-handling.md#Pattern 5: Let Errors Handle the Long Tail Instead of Bloating Descriptions -->
## Let errors handle the long tail

If a model gets the call right 90%+ of the time, do not cram every edge case into the description; let good errors handle the remaining 10%.

- **Exhaustive descriptions** cover every case upfront but waste tokens on every call, even when the model would have been right.
- **Minimal descriptions plus rich errors** keep the initial context lean and inject detail only when needed.

Example `search_contacts` ("Search for contacts by name, email, or company."): an empty query returns "Query cannot be empty. Provide a name, email, or company name."; `limit > 100` returns "Limit N exceeds maximum of 100. Call search_contacts(query='...', limit=100) instead."; no results returns a valid (not error, `isError: false`) result: "No contacts found for '...'. Try a broader search term or check spelling. You can also use list_companies() to browse available companies."

This matters most for APIs with many endpoints: stuffing documentation into descriptions overloads context (30+ detailed tools degrade performance). Caveat: core usage patterns still belong in the description; only edge cases and rare failure modes belong in errors. Length rule: `descriptions-structure-and-length.md`.

<!-- src: audit-agentic-mcp/references/patterns/error-handling.md#Pattern 6: Distinguish "Prevented" from "Failed" in Error Framing -->
## Distinguish "prevented" from "failed"

When a tool catches bad input before executing, it prevented a problem; it did not fail. The wording changes the agent's whole subsequent behavior.
- "Error detected, operation canceled" triggers frustration loops: the agent assumes it broke something and produces unproductive recovery sequences.
- "Caught early, here's how to fix it" says the system is working with the agent and encourages a single corrective retry.

Bad (punitive): "Error: invalid date. Operation canceled." The agent may abandon the approach, apologize to the user, or try a different strategy, all unnecessary.

Good (preventive): "The date 2023-11-15 is in the past — schedule_meeting requires a future date. Use a date after 2025-01-15 and retry with schedule_meeting(date='2025-01-20', ...)." Code variant: "Great catch — {date} is in the past. Use a future date (after {today}) and retry: schedule_meeting(date='<future_date>', title='{title}')".

Key distinction: `isError: true` tells the protocol something went wrong; the text tells the agent whether to feel bad or just adjust one parameter. The text matters more than the flag.

<!-- src: audit-agentic-mcp/references/patterns/error-handling.md#Pattern 7: Avoid "Not Found" Phrasing — Return What Exists Instead -->
## Avoid "not found" phrasing; return what exists

"X not found" anchors the LLM on failure. Drop the negative prefix and return the available options; the model picks the closest match itself.

Bad: "Module 'color' not found. Available modules: fs, http, path, crypto." The agent fixates on "not found" and may tell the user the module does not exist, try to install it, or invent an alternative before reading your list.

Good: "Available modules: fs, http, path, crypto. Select one to proceed." (`isError: true`). In code: when the name is not in the set, return "Available modules: {sorted list}. Retry load_module(name='<module>') with one of these."; otherwise "Loaded {name} successfully."

The same principle applies broadly:
- Users: not "User not found" but "Matching users: alice, bob, carol."
- Files: not "File missing" but "Files in directory: config.yaml, schema.json."
- Endpoints: not "Invalid action" but "Supported actions: create, read, update, delete."

"Not found" primes a failure-recovery pattern; a list of options primes a selection pattern, which is far more productive. This wording applies to the message text, not the status: classify the failure honestly in the envelope (`../decisions/error-strategy.md`).

<!-- src: audit-agentic-mcp/references/patterns/error-handling.md#Pattern 9: Return Normalized Inputs in Every Response -->
## Return normalized inputs in every response

When the server accepts flexible input and normalizes it ("yesterday" -> "2024-01-15"), include the normalized values in the response. This teaches the canonical format and improves every later call.

Without it, the agent invents variations ("yesterday", "the day before", "24 hours ago"), each a parsing gamble. With it:

```json
{"result": {"events": [{"title": "Standup", "time": "09:00"}]},
 "normalized_inputs": {"date": "2025-01-15", "note": "Interpreted 'yesterday' as 2025-01-15"}}
```

After seeing this once, the agent uses `"2025-01-15"` directly. Same principle for rate-limit errors, return structured retry info:

```json
{"rate_limited": true, "retry_after_seconds": 30, "reset_at": "2025-01-15T10:05:00Z"}
```

The principle: every response is a training signal. Return the canonical form of what you understood and the agent converges on clean inputs fast. Input flexibility: `schemas-flat-and-sized.md`.
