# Iterate on an MCP server with hot reload and the Inspector

> Read when: you are setting up the local edit-test loop for an MCP server, or restarting the server by hand after every change.

<!-- src: audit-agentic-mcp/references/patterns/transport-and-ops.md#3. Use Hot Reload During Development -->
## Use hot reload and keep the Inspector open

Kill-restart cycles during development are slow and break your flow. Use a dev runner that watches files and restarts the server automatically, and keep the MCP Inspector open on the same server.

Development workflow:

```
1. Start:     run the framework's dev command with the Inspector attached
2. Open:      MCP Inspector at the URL it prints on start (`npx @modelcontextprotocol/inspector`)
3. Edit:      Modify tool descriptions, add parameters, fix bugs
4. Automatic: Server restarts, Inspector reconnects
5. Test:      Call tools in Inspector to verify changes
6. Repeat
```

Additional tools, as shell:

```bash
npx @modelcontextprotocol/inspector@latest   # GUI for testing tool calls
claude mcp add <name> <command>              # quick local registration in Claude Code
```

Pro tip: keep the Inspector open while iterating on tool descriptions. You see immediately how schema changes affect the tool discovery payload. Make tool functions directly callable in unit tests (no protocol overhead) and reserve the remote call path for integration tests; see [ops-testing-layers.md](ops-testing-layers.md).

The FastMCP commands (`fastmcp dev inspector server.py`, `fastmcp dev`) and the FastMCP 3.0 direct-call testing example are in [python](../frameworks/mcp-python/transport-and-ops.md).

Sources: FastMCP 3.0 release notes, NearForm.
