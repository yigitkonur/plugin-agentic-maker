# MCP and CLI hybrids, kill criteria, keep criteria

> Read when: you have decided MCP may be the wrong abstraction, or you keep MCP and need hybrid patterns, red flags, keep signals, and the order in which to optimize.

<!-- src: audit-agentic-mcp/references/patterns/mcp-vs-cli.md#6. Hybrid Patterns That Usually Beat Pure MCP -->
## Hybrid patterns that usually beat pure MCP

<!-- src: audit-agentic-mcp/references/patterns/mcp-vs-cli.md#6.1 MCP Control Plane, CLI Execution Plane -->
### MCP control plane, CLI execution plane

Use MCP for auth, approval, tool discovery, tenant isolation. Use CLI for read-heavy operations, local transforms, batch processing, shell-native execution. Right when you need a governed remote interface for agents but the real work is still cheap command execution.

<!-- src: audit-agentic-mcp/references/patterns/mcp-vs-cli.md#6.2 CLI First, MCP For Stateful Or Governed Calls -->
### CLI first, MCP for stateful or governed calls

Use CLI for simple reads, local automation, developer workflows. Use MCP only for session-heavy operations, governed writes, user-scoped remote access. This is the most pragmatic split for coding agents.

<!-- src: audit-agentic-mcp/references/patterns/mcp-vs-cli.md#6.3 MCP Gateway With CLI Backend -->
### MCP gateway with CLI backend

If the CLI is excellent but governance is mandatory, keep the CLI behind the wall and put the wall in MCP:

- the gateway handles auth, audit, policy, and approval
- backend execution uses CLI or shell wrappers
- the agent sees a controlled tool surface instead of raw shell

This is better than exposing broad shell access through policy exceptions alone.

<!-- src: audit-agentic-mcp/references/patterns/mcp-vs-cli.md#7. Kill Criteria: Signs The MCP Server Is The Wrong Abstraction -->
## Kill criteria: signs the MCP server is the wrong abstraction

Treat these as red flags, not automatic verdicts:

- the server is a thin wrapper around an existing CLI with no additional auth or discovery value
- the server eagerly exposes dozens of endpoint-level tools that agents barely use
- the workflow is local, single-tenant, and developer-only
- the main problem is "the agent needs instructions" rather than "the system needs governed access"
- tool definitions dominate context cost before the first call
- most tool responses are raw upstream JSON instead of curated results
- auth problems, timeouts, and schema bloat are the biggest complaints in practice

If several are true, the best optimization may be to reduce the MCP surface, move parts back to CLI, or replace the server with a skill plus CLI workflow.

<!-- src: audit-agentic-mcp/references/patterns/mcp-vs-cli.md#8. Keep Criteria: Signs The MCP Server Is Worth Optimizing -->
## Keep criteria: signs the MCP server is worth optimizing

Invest in the server when several of these are true:

- users connect personal or tenant-scoped accounts
- the system needs approval and audit semantics at the tool layer
- stateful sessions are central to the tool design
- the same tool surface serves multiple clients or models
- schema-driven discovery materially improves tool use
- the operator cannot assume shell access or CLI literacy

In those cases, optimize the server rather than migrating away from MCP.

<!-- src: audit-agentic-mcp/references/patterns/mcp-vs-cli.md#9. If You Keep MCP, Optimize In This Order -->
## If you keep MCP, optimize in this order

1. Confirm the server is justified against the criteria above.
2. Shrink the exposed tool surface before rewriting handlers.
3. Add progressive discovery, lazy loading, or gateway filtering when tool count is high (`decisions/tool-count.md`).
4. Curate tool outputs so the model sees task-shaped responses, not raw upstream payloads.
5. Fix auth, approval, and transport reliability before polishing descriptive text.
6. Separate protocol errors from business-logic failures (`decisions/error-strategy.md`).

This order matters. A beautifully described server with the wrong abstraction boundary is still the wrong server.
