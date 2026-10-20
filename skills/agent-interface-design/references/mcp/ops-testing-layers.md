# Test an MCP server in three layers

> Read when: you are debugging a tool, choosing how to verify an MCP change, or deciding when to involve an LLM in testing.

<!-- src: audit-agentic-mcp/references/patterns/testing.md#Testing -->
Test MCP servers in layers: evaluation-driven development with realistic workflows (`ops-evals.md`), the MCP Inspector for isolated debugging (this file), auto-refactoring from transcripts (`ops-evals.md`), LLM-based usability review (`ops-usability-review.md`), systematic tool selection evals (`ops-tool-selection-evals.md`), and file hashing to prevent agent reprocessing loops (`ops-execution-cache.md`).

After any applied optimization, pick one live verification route and state it in the audit output:

- a repeatable command-line smoke check for stdio or Streamable HTTP, with JSON scripting (a companion tool for this may exist if installed);
- the MCP Inspector for interactive protocol debugging;
- unit or integration tests for deterministic code paths.

<!-- src: audit-agentic-mcp/references/patterns/testing.md#2. Test Tools with MCP Inspector Before Involving an LLM -->
## Inspector before an LLM

Do not debug tool behavior through the LLM. Use the MCP Inspector to call tools directly and inspect raw JSON-RPC payloads. Launch command and package: `../fresh/mcp-testing-tools.md`.

What to verify with the Inspector:

1. Tool discovery: does `tools/list` return correct schemas?
2. Input validation: do bad parameters produce clear errors?
3. Response format: are responses structured as expected?
4. Error handling: do failures return `isError: true` with guidance?
5. No stdout pollution: does the server write only JSON-RPC to stdout? (See `ops-stdio-hygiene.md`.)

The debugging loop:

```
1. REPRODUCE  -> Capture exact input that triggers the bug
2. CHECK LOGS -> Pull stderr logs for stack traces
3. ISOLATE    -> Disable all but one tool to narrow scope
4. INSPECTOR  -> Send crafted JSON-RPC payloads
5. FIX        -> Run the reproduced case + full test suite
```

Three layers of testing:

1. **Unit tests:** test business logic functions directly (no MCP overhead).
2. **Integration tests:** spin up the MCP server, call tools via the protocol.
3. **Eval tests:** run multi-step agent workflows with an actual LLM (`ops-evals.md`).

Start from layer 1 and involve the LLM (layer 3) only after layers 1-2 pass. This saves time and API costs.

Non-obvious tip: temporarily disable all but one tool to see whether an issue persists. This isolates whether the problem is tool-specific or systemic.

Sources: Stainless (error handling and debugging MCP servers), NearForm (implementing MCP), the MCP Inspector package.
