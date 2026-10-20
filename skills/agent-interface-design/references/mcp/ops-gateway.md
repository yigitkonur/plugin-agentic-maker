# Put cross-cutting concerns in a gateway

> Read when: you run several MCP servers and need shared auth, rate limiting, naming, lifecycle or per-call policy without duplicating it in each server.

<!-- src: audit-agentic-mcp/references/patterns/composition.md#1. Use a Meta-Server for Cross-Cutting Concerns -->
## Meta-server for cross-cutting concerns

When running multiple MCP servers, do not duplicate auth, rate limiting and logging in each one. Build a lightweight meta-server (gateway) that handles cross-cutting concerns and delegates to domain-specific servers. The gateway runs a middleware chain before routing (auth, rate limit with `max_requests=100` per `window_seconds=60`, audit log), routes to the backend by namespace prefix (`github` from `github_create_pr`), then runs the chain in reverse over the result. Code: `../frameworks/mcp-python/composition.md`.

What the gateway handles:

- **Authentication:** verify user tokens before forwarding.
- **Authorization:** check per-tool permissions.
- **Rate limiting:** prevent abuse across all backend servers.
- **Audit logging:** a single log stream for all tool calls.
- **Response transformation:** namespace tool names, filter sensitive fields.

The gateway pattern also enables:

- Lazy loading of backend servers (connect only when the first tool is called).
- Failover between redundant server instances.
- Version routing (send 20% of traffic to v2).
- Tool visibility control per user or session.

Framework-level mounting with namespaces and an auth transform is shown in `../frameworks/mcp-python/composition.md`.

Sources: NearForm (implementing MCP), FastMCP 3.0 announcement, MCP specification.

<!-- src: audit-agentic-mcp/references/patterns/composition.md#6. Use a Gateway/Proxy for Multi-Server Orchestration -->
## Gateway or proxy for multi-server orchestration

Running multiple MCP servers creates operational problems: tool-name collisions, resource waste from idle servers, no unified discovery, and cascading failures. A gateway proxy between the client and the server fleet solves all of them. It handles:

- server-prefixed naming (`web__search`, `db__query`) to avoid collisions (`naming: 'prefixed'`);
- on-demand server lifecycle;
- circuit breaking for unreachable servers;
- a unified `tools/list` across all servers.

Declare the servers and let the gateway manage lifecycle. Reference settings from the source configuration: a `web` server with `lazy: true` (starts only when a tool is called), `idleTimeout: 120_000` (stop after 2 min of inactivity) and `healthCheck: { interval: 30_000, timeout: 5_000 }`; a `db` server with `lazy: true`, `idleTimeout: 300_000` and `maxRetries: 3` (circuit breaker after 3 failures). The client sees one server with all tools. Config code: `../frameworks/mcp-ts/composition.md`. Existing gateway products: `../fresh/mcp-gateway-tools.md`.

When you need this:

- 3+ MCP servers run simultaneously.
- Tool names conflict across servers.
- Resource-constrained environments where idle servers waste memory.
- Production deployments need circuit breaking and monitoring.

When you do not: with 1-2 servers and no name conflicts, direct connections are simpler. Do not add a gateway for the sake of architecture.

Sources: MCPJungle and MetaMCP project documentation; r/mcp community discussion.

<!-- src: audit-agentic-mcp/references/patterns/composition.md#7. Zero-Trust Policy Gateway -->
## Zero-trust policy gateway

Wrap the MCP server in a policy execution gateway that evaluates every tool call against a declarative policy before dispatch. The gateway validates permissions, enforces constraints and signs job tickets, all without modifying individual tool handlers.

```
LLM Client -> Policy Gateway -> Tool Handler
                   |
           policy.json (rules)
           HMAC ticket signing
           audit log
```

The gateway checks, in order: the tool is in `allowed_tools` (else error `Tool "<name>" is not in the allowed_tools list.`); the session `role` matches `require_role` (else the error names the required and current role); every `require_context` field is present in the session (else `Missing required session context: <field>`). It then signs a job ticket (HMAC-SHA256 over tool name, params and timestamp, keyed by a `GATEWAY_SECRET` environment value), writes the ticket and session to the audit log, and calls the handler. Code: `../frameworks/mcp-ts/composition.md`.

`policy.json` example:

```json
{
  "allowed_tools": ["read_file", "list_directory", "create_issue", "deploy_staging"],
  "per_tool": {
    "deploy_staging": {
      "require_role": "deployer",
      "require_context": ["project_id", "branch"]
    },
    "create_issue": {
      "require_context": ["github_token"]
    }
  }
}
```

Policy fields per tool: `max_params` (constraints on parameter values), `require_context` (required session fields), `require_role`. A centralized policy gateway decouples authorization logic from tool handlers, allows policy changes without code deployments, and provides a tamper-evident audit trail for all tool invocations. Security context: `security/least-privilege-and-confirmation.md`.

Sources: Stacklok policy gateway pattern; zero-trust design principles for LLM tool execution.
