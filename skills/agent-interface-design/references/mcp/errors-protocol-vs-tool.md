# MCP errors: isError versus protocol errors, and teaching messages

> Read when: a tool can fail and you must decide which error channel to use and what the message should say.

<!-- src: audit-agentic-mcp/references/patterns/error-handling.md#Error Handling Patterns -->
Design MCP error responses that let the agent recover instead of hitting a dead end. This file covers the channel choice and the content of a message; framing, retry limits and normalized inputs are in `errors-framing-and-recovery.md`; loop detection is in `errors-loop-breaker.md`. Strategy across CLI and MCP: `../decisions/error-strategy.md`. Exit codes for CLIs: `../cli/exit-codes.md`. Code: `../frameworks/mcp-python/error-handling.md`.

<!-- src: audit-agentic-mcp/references/patterns/error-handling.md#Pattern 1: Use isError in the Result Object, Not Protocol-Level Errors -->
## Use isError in the result, not a protocol-level error

MCP has two error paths; choosing the wrong one kills agent recovery.

**Protocol-level error** (JSON-RPC `error` field): the tool was not found, the request was malformed, or the server crashed. The LLM typically never sees it; the client swallows it.

```json
{"jsonrpc": "2.0", "id": 1, "error": {"code": -32001, "message": "Request Timeout"}}
```

**Tool-call error** (`isError: true` in `result`): the tool ran and the operation failed. This is injected into the LLM's context so the model can reason about it and recover.

```json
{"jsonrpc": "2.0", "id": 2,
 "result": {"content": [{"type": "text",
   "text": "Cannot terminate instance while it is running. Call stop_instance(instance_id='i-abc123') first, then retry."}],
  "isError": true}}
```

The rule: use protocol-level errors only for actual protocol failures (bad JSON, unknown method, server crash). For every business-logic failure (validation, permission, resource not found) use `isError: true` in the result so the LLM sees the message and can adjust. A thrown protocol error for a business failure gives the model a generic "tool call failed" and nothing to fix.

<!-- src: audit-agentic-mcp/references/patterns/error-handling.md#Pattern 2: Make Error Messages Educational, Not Technical -->
## Make error messages educational

An error message IS the documentation at that moment; the model has no other source of truth.

Bad (a real database-platform MCP example): `{"error": "Unauthorized"}`. It stops the model cold: it concludes it lacks permissions and gives up.

Good: `{"error": "Project ID 'proj_abc123' not found or you lack permissions. To see available projects, use the listProjects() tool.", "isError": true}`.

Error message checklist:
1. **Name the specific field** that caused the failure.
2. **State the expected format** or valid values.
3. **Show an example** of correct input.
4. **Suggest a recovery action** with a specific tool name.

Template: "Parameter '{field}': {problem}. Expected: {expected}." plus, when a recovery tool exists, " Use {recovery_tool} to get valid values." Worked example: field `start_date`, problem "Date '2024-07-31' is in the past", expected "A future date in YYYY-MM-DD format" gives "Parameter 'start_date': Date '2024-07-31' is in the past. Expected: A future date in YYYY-MM-DD format." Helper code: `../frameworks/mcp-python/error-handling.md`.

If a model gets the call right 90%+ of the time and can self-correct from a good error the other 10%, you do not need exhaustive descriptions for every edge case. Errors handle the long tail (details in `errors-framing-and-recovery.md`).

<!-- src: audit-agentic-mcp/references/patterns/error-handling.md#Pattern 3: Embed Recovery Tool Names Directly in Error Messages -->
## Embed recovery tool names in the error

When a call fails, do not only say what went wrong; tell the model which tool to call next.

State-change prerequisite error: "You can't terminate an instance while it is running. Call stop_instance(instance_id='i-abc123') first, then retry terminate_instance()." With `isError: true`. In code, check the instance state and name the stop call with the real `instance_id`, tell the model to wait for the `stopped` state, then retry `terminate_instance(instance_id='...')`.

Validation with a corrected suggestion: "The requested travel date cannot be in the past. You asked for July 31 2024 but today is July 25 2025. Did you mean July 31 2025?" (`isError: true`).

Key principle: include the actual parameter values the model should use, not just the tool name. Do not make the model work out the arguments; spell them out.

Steering text inside errors is still tool output; follow `../decisions/steering-contract.md` for namespacing and `allowed_next_tools` when the next step is mandatory.
