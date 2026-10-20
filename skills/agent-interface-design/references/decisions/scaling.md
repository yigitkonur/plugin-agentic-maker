# Scaling an MCP server architecture

> Read when: one MCP server may no longer be enough and you must choose between a gateway, session pooling, background tasks, or multi-agent coordination.

<!-- src: audit-agentic-mcp/references/decision-trees/scaling.md#Scaling MCP Server Architecture | audit-agentic-mcp/references/decision-trees/scaling.md#Decision Tree -->
## Decision tree

A single MCP server works until it does not. Pick the scaling dimension that is the actual bottleneck. Source-reported pooling throughput figures are in `fresh/decision-tree-benchmarks.md`.

```
START: Is a single MCP server sufficient?
|
+-- YES (single domain, <20 tools, one model consumer)
|   +-- Keep it simple. Direct stdio or HTTP connection.
|   +-- Focus on tool design quality, not architecture.
|   +-- --> mcp/ops-* for session scoping
|
+-- NO -- which scaling dimension is the bottleneck?
    |
    +-- MULTIPLE DOMAINS (need 3+ servers)
    |   +-- Do tool names conflict across servers?
    |   |   +-- YES --> Use a gateway/proxy with prefixed naming
    |   |   |   (web__search, db__query avoids collisions)
    |   |   +-- NO  --> Direct connections may still work
    |   +-- Need unified tool discovery across all servers?
    |   |   +-- YES --> Gateway with unified tools/list
    |   +-- Resource-constrained environment?
    |   |   +-- YES --> Lazy server startup + idle timeout
    |   |   |   (start on first tool call, stop after 2min idle)
    |   +-- Need circuit breaking for unreachable servers?
    |   |   +-- YES --> Gateway with maxRetries + health checks
    |   +-- --> mcp/design-* (composition)
    |   |
    |   +-- Design each server for composability:
    |       +-- Each server specializes in one domain
    |       +-- Return data + scaffolds, not finished outputs
    |       +-- Include next_steps referencing tools from OTHER servers
    |       +-- Let the LLM orchestrate cross-server workflows
    |       +-- --> mcp/design-* (composition)
    |
    +-- HIGH THROUGHPUT (many concurrent requests)
    |   +-- Use session pooling (shared pool of 10 sessions)
    |   +-- Externalize session state to Redis
    |   |   (any pooled connection can serve any request)
    |   +-- For HTTP with a fixed replica count: load balancer with session affinity
    |   |   (to autoscale, externalize state and drop affinity)
    |   +-- --> mcp/ops-*
    |
    +-- LONG-RUNNING OPERATIONS (>30 second tool calls)
    |   +-- Return task IDs immediately, let agent poll for results
    |   +-- Use FastMCP @mcp.tool(task=True) or custom async queue
    |   +-- Agent can do other work while waiting
    |   +-- --> mcp/ops-*
    |
    +-- MULTI-AGENT COORDINATION (multiple agents sharing state)
        +-- Use append-only event log (not shared mutable state)
        |   Avoids last-write-wins conflicts and race conditions
        +-- Event types: observation, decision, action, result, handoff
        +-- Agents read_log at session start, log_event for all actions
        +-- Use supersedes field for corrections without erasing history
        +-- --> mcp/design-* (agentic patterns)
```

<!-- src: audit-agentic-mcp/references/decision-trees/scaling.md#Key Decision Factors -->
## Key decision factors

| Factor | Options | Recommendation |
|---|---|---|
| Server count | 1-2 vs 3+ | Gateway only needed at 3+ or when names conflict |
| Throughput need | Low vs high concurrent | Session pooling gives a large throughput improvement (figures: `fresh/decision-tree-benchmarks.md`) |
| Operation duration | <30s vs >30s | Background tasks for anything over 30s |
| State sharing | Single agent vs multi-agent | Append-only log for multi-agent; avoid shared mutables |
| Server lifecycle | Always-on vs on-demand | Lazy startup + idle timeout for resource efficiency |
| Session state | In-memory vs externalized | Externalize to Redis for horizontal scaling |

<!-- src: audit-agentic-mcp/references/decision-trees/scaling.md#When to Re-evaluate -->
## When to re-evaluate

- When adding a 3rd MCP server (consider gateway).
- When throughput drops under load (add session pooling).
- When tool calls start timing out (add background task pattern).
- When a second agent needs to read the first agent's work (add event log).
- When deploying to Kubernetes (externalize all state).
