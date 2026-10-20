# MCP vs CLI: should this be an MCP server?

> Read when: you audit or design an MCP server and the real question may be whether the workflow belongs in MCP at all, before you touch schemas or descriptions.

<!-- src: audit-agentic-mcp/references/patterns/mcp-vs-cli.md#MCP vs CLI: Should This Be An MCP Server? | audit-agentic-mcp/references/patterns/mcp-vs-cli.md#1. Fast Recommendation -->
## Fast recommendation

Do not assume every agent-accessible integration should be an MCP server.

- Keep the workflow in CLI when it is developer-facing, command-shaped, and already well served by a strong CLI.
- Keep or build MCP when the requirement is governed remote access, typed discovery, or stateful sessions.
- Choose a hybrid when MCP should own auth or approvals but CLI should own execution (`decisions/mcp-vs-cli-hybrids.md`).
- Choose a skill when the missing piece is workflow guidance, not a new runtime surface.

When auditing an existing MCP server, open this file before touching schemas or tool descriptions if any of these is true:

- the repo already depends on a mature first-party CLI
- the server mostly shells out to local commands
- the tools are thin wrappers over REST endpoints
- the workload is mostly one-shot and stateless
- the pain is token cost, auth flakiness, or unused tool bloat

<!-- src: audit-agentic-mcp/references/patterns/mcp-vs-cli.md#2. What The Official Docs Establish -->
## What the official docs establish

| Documented fact | Why it matters |
|---|---|
| MCP is a JSON-RPC protocol with `stdio` and Streamable HTTP transports. | MCP is a protocol decision, not just a transport detail. It can be local or remote, but it always adds protocol semantics. |
| MCP servers expose tools with typed `inputSchema`, plus resources and prompts. | Keep MCP when discoverable, typed tool contracts are part of the product value. |
| HTTP-based MCP auth is specified around OAuth 2.1 style flows and metadata discovery; `stdio` should use environment credentials instead. | MCP is strongest for governed remote access. Local shell-style credential handling is not where it shines. |
| Anthropic and OpenAI document approvals, allowlists, deferred loading, and strong warnings about untrusted third-party servers. | MCP deserves the overhead when trust boundaries and approvals are part of the requirement. |
| Shell and local-shell tools execute in the caller's runtime, with safety coming from sandboxing, hooks, allowlists, and permission prompts. | CLI-first is operationally simpler, but the caller owns the local blast radius. |

Primary doc links (protocol architecture, transports spec of November 25, 2025, authorization spec of June 18, 2025, vendor MCP guides): `fresh/mcp-vs-cli-benchmarks.md`.

<!-- src: audit-agentic-mcp/references/patterns/mcp-vs-cli.md#3. Use MCP When The Protocol Features Are The Product -->
## Use MCP when the protocol features are the product

An MCP server is justified when the protocol gives you something a CLI cannot give cleanly.

Strong MCP signals:

- per-user OAuth, token refresh, approval, or revocation
- multi-tenant SaaS or user-specific data boundaries
- multiple clients or models need the same tool surface
- the workflow depends on remote discovery and typed schemas
- the tool maintains state across calls
- the integration is remote-first and connector-like rather than process-like

Good MCP examples: SaaS connectors where end users bring their own account; governed write operations with approval steps; browser or session-based automation; shared internal platform tools consumed by several agent runtimes.

If those requirements are absent, be skeptical that the server should exist.

<!-- src: audit-agentic-mcp/references/patterns/mcp-vs-cli.md#4. Choose CLI Instead When The Work Is Really Command Execution -->
## Choose CLI when the work is command execution

Do not keep an MCP server just because the agent can call tools. Keep it only if the protocol layer is earning its keep.

Strong CLI signals:

- a mature CLI already exists
- the workflow is mostly stateless and one-shot
- the operator is a developer in a trusted environment
- shell composition, files, pipes, and redirects are central to the task
- JSON output and non-interactive flags already solve the data contract
- the main value is cheap execution, not typed remote discovery

Good CLI examples: `gh`, `git`, `kubectl`, `aws`, `docker`, `jq`, `curl`, `stripe`; repo maintenance, deployment, infra inspection, CI helpers; batch transforms where the shell can do the mechanical work once the model decides the plan.

If your MCP server mostly maps one remote endpoint to one tool, and a good CLI already exists, shrinking or replacing the MCP layer is usually the correct optimization.

<!-- src: audit-agentic-mcp/references/patterns/mcp-vs-cli.md#5. Use A Skill Instead When The Missing Piece Is Workflow Knowledge -->
## Use a skill when the missing piece is workflow knowledge

Do not build an MCP server to explain how to use existing tools. Use a skill when:

- the runtime capability already exists as CLI or API
- the agent needs a playbook, order of operations, or house rules
- the problem is routing, not transport
- the system only needs static guidance or lightweight dynamic context injection

Examples: "When triaging GitHub issues, prefer `gh --json` with these fields." "For deploy checks, run these five commands, then stop if this exit code appears." That is a skill plus CLI problem, not an MCP server problem.

<!-- src: audit-agentic-mcp/references/patterns/mcp-vs-cli.md#11. Security Note -->
## Security note

MCP is not automatically safer than CLI, and CLI is not automatically simpler in production. The real distinction is where you want control:

- CLI concentrates power in the local runtime, then constrains it with sandboxing, allowlists, hooks, and permissions.
- MCP concentrates control in a mediated protocol surface, then constrains it with auth, approvals, policy, and server trust.

If untrusted inputs, sensitive data, and state-changing actions can meet in one autonomous flow, apply a stricter security model. Meta's "Rule of Two" (October 31, 2025; link in `fresh/mcp-vs-cli-benchmarks.md`) is a useful framing tool even though it is not MCP-specific.

<!-- src: audit-agentic-mcp/references/patterns/mcp-vs-cli.md#12. Decision Rules To Apply In This Skill -->
## Decision rules to apply

1. Before optimizing the server, decide whether the workflow should remain in MCP at all.
2. Recommend CLI when a mature CLI already covers the workflow and protocol features are not central.
3. Recommend a skill when the missing piece is workflow guidance, not runtime capability.
4. Recommend hybrid when auth and governance need MCP but execution still looks like deterministic command work.
5. Recommend MCP only when protocol features are clearly justified by the user or deployment model.

Dated community and benchmark evidence (CLI vs MCP token and completion numbers, practitioner themes): `fresh/mcp-vs-cli-benchmarks.md`.
