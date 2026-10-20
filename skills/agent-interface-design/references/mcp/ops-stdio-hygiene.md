# Keep stdout pure JSON-RPC

> Read when: a stdio MCP server fails mysteriously, or you are adding any logging, banner or health output to a server.

<!-- src: audit-agentic-mcp/references/patterns/transport-and-ops.md#1. Keep stdout Pure JSON-RPC -- All Logs to stderr -->
## Only JSON-RPC on stdout, everything else on stderr

The number one cause of mysterious MCP server failures: a stray `print()` or `console.log()` on stdout corrupts the JSON-RPC message stream. The rule: stdout must contain only valid JSON-RPC messages. Everything else goes to stderr. Never use `print()` (Python) or `console.log()` (Node); configure logging to stderr (`logging` with `stream=sys.stderr`, `console.error`) and use the logger.

Common traps:
- Third-party libraries that write to stdout (disable their logging or redirect).
- Debugging `print` statements left in production code.
- Framework startup banners (suppress them).
- Health check responses written to stdout instead of HTTP.

How to verify (neutral shell check; any error means stdout pollution):

```bash
node my-server.js 2>/dev/null | jq .
```

Code for Python and Node loggers: [python](../frameworks/mcp-python/transport-and-ops.md), [typescript](../frameworks/mcp-ts/transport-and-ops.md). Related hard rules: [hard-rules.md](hard-rules.md).

Sources: Stainless (error handling and debugging MCP servers), NearForm.
