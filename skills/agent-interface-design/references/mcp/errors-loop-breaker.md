# Break agent retry loops with a circuit breaker

> Read when: an agent may call the same failing tool again and again and the server must stop it from outside the model.

Code: `../frameworks/mcp-python/error-handling-recovery.md`. Retry wording inside errors: `errors-framing-and-recovery.md`.

<!-- src: audit-agentic-mcp/references/patterns/error-handling.md#Pattern 8: Build Circuit Breakers for Agent Loop Detection -->
## Build circuit breakers for loop detection

Agents cannot detect their own loops: from the LLM's perspective every retry is a fresh attempt with renewed optimism. Detect and break loops outside the LLM's decision-making.

The problem: an agent calls `update_record(id=42, status="active")`, gets a validation error, "fixes" the call, sends the exact same parameters, gets the same error, and repeats indefinitely. The LLM genuinely believes each attempt differs. A reported incident cost $63 overnight.

Solution, hash-based state tracking:
1. Hash the tool name plus all parameters (sorted) into a short digest (the example uses the first 16 hex chars of SHA-256).
2. Keep timestamps per digest and prune those older than the window.
3. When a digest reaches `max_repeats` inside `window_seconds`, return an `isError: true` result instead of executing: "Loop detected: {tool_name} called {max_repeats} times with identical parameters in {window}s. Stop retrying and ask the user for guidance."
4. Wire the check into the single tool-call handler, before `execute_tool`.

What to hash: the full execution state: tool name, all parameters and any file references. Not just the tool name: `search("foo")` and `search("bar")` are different calls, but `search("foo")` three times in a row is a loop.

Tuning: defaults are `max_repeats=3` within `window_seconds=120` (3 repeats within 2 minutes). Tighten for fast tools (API lookups); loosen for tools with legitimate retries (file uploads with transient failures).

Pair this server-side breaker with the in-message retry limit (3 attempts, then fallback) from `errors-framing-and-recovery.md`; the breaker covers models that ignore the message.
