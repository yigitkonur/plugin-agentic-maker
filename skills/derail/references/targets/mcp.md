# Target: an MCP server

> Read when: the target is an MCP server (stdio command or a config file) and you want to see an agent use its tools.

**Exposure:** `--mcp-config <file>` with `--strict-mcp-config`, so only the target's server is loaded; or `target: mcp-stdio:<command>` and the runner writes the config. The tools are allowed as `mcp__<server>`; give the scenario no other tool the task does not need. Secrets and a build step are the scenario's `env:` and `build:`; a server that needs credentials you do not want a test worker to hold is audited statically instead.

**Lens:**
1. **Tool selection (M7):** which tool did it pick, was it the right one, did it alternate between two?
2. **Arguments:** rejected calls, guessed enums, required fields it missed.
3. **Responses (O7, O8):** did it read the answer correctly; was a response so large it crowded out the task; was truncation visible?
4. **Errors (C5):** did an error say what to change, and did a retry follow it?
5. **Budget:** the definition cost is measured separately by `agentic-maker probe mcp --budget`; the trace shows what the model did with what it was given.

**Typical scenarios:** a task that needs one tool; one that needs a sequence of three; one that triggers a validation error; one with a large result set.
