# Machine-readable error taxonomy and the shared event log

> Read when: you want agents to decide retry versus stop from a fixed error vocabulary, or several agents share one server and need conflict-free coordination.

Part of the agentic patterns; ordering and guards are in `patterns-guarded-workflows.md`. Code (TypeScript): `../frameworks/mcp-ts/agentic-patterns-serf.md`, `../frameworks/mcp-ts/agentic-patterns-stages.md`.

<!-- src: audit-agentic-mcp/references/patterns/agentic-patterns.md#4. SERF: Machine-Readable Error Taxonomy for Agents -->
## SERF: machine-readable error taxonomy for agents

Return errors in a structured, fixed taxonomy so the LLM decides programmatically whether to retry, switch tools, escalate or stop, instead of parsing prose. The SERF framework (Structured Error Recovery Framework) was proposed in arXiv:2603.13417 ("Bridging Protocol and Production", Srinivasan, 2026).

| `error_category` | `retryable` | Default `suggested_actions` | Meaning |
|---|---|---|---|
| `INVALID_PARAMS` | false | `fix_params_and_retry` | Schema/validation failure; do not retry as-is |
| `RESOURCE_NOT_FOUND` | false | `search_for_resource`, `list_resources` | Target does not exist; check the ID |
| `RESOURCE_EXHAUSTED` | true | `retry_after_delay`, `reduce_request_size` | Quota; retry after a delay |
| `PERMISSION_DENIED` | false | `check_permissions`, `use_different_credentials` | Auth failure; escalate or use other credentials |
| `RATE_LIMITED` | true | `wait_and_retry` | Explicit rate limit; retry after `retry_after_ms` |
| `INTERNAL_ERROR` | true | `retry_with_backoff`, `report_issue` | Server-side failure; retry with backoff |

Error shape: `error_category`, `message` (human readable), `retryable` (bool), optional `retry_after_ms` (for `RATE_LIMITED` and `RESOURCE_EXHAUSTED`), `suggested_actions` (list), optional `param_hints` (field -> fix hint, for `INVALID_PARAMS`). Example: `RATE_LIMITED`, "GitHub API rate limit exceeded", `retry_after_ms: 60000`, `suggested_actions: ["wait_60s_then_retry"]`.

Agent behavior contract: errors always include `retryable` and `error_category`. If `retryable=false`, stop and report to the user; if `RATE_LIMITED`, wait `retry_after_ms`; if `INVALID_PARAMS`, inspect `param_hints`. Prose errors get retried inconsistently; a taxonomy gives deterministic retry logic and prevents both premature give-ups and infinite loops. The CLI error classes are a different vocabulary (`../decisions/error-strategy.md`); do not mix the two in one envelope.

<!-- src: audit-agentic-mcp/references/patterns/agentic-patterns.md#5. Shared Context: Append-Only Event Log for Multi-Agent Coordination -->
## Shared context: append-only event log for multi-agent coordination

When several agents share one server they need coordination that avoids last-write-wins conflicts and keeps the history of what each did. An append-only event log gives both.

Why not shared mutable state: two agents that read-then-write the same record silently clobber each other; locks add deadlock risk. With an append-only log, agents only write new entries and never update old ones, so concurrent writes are safe.

Entry shape: `id`, `agent_id`, `timestamp` (ISO 8601), `type` (enum `observation`, `decision`, `action`, `result`, `handoff`), `payload`, optional `confidence` (0.0-1.0), optional `supersedes` (ID of an earlier entry this revises). Tools: `log_event(agent_id, type, payload, confidence?, supersedes?)` appends and returns "Logged event {id}"; `read_log(since?, agent_id?, type?, limit=50)` returns the filtered tail. The example keeps the log in memory; use Redis or Postgres for persistence.

Coordination pattern: each agent calls `read_log` at session start to learn what others did, and calls `log_event` with type `handoff` when passing work on. `supersedes` allows a correction without erasing history. Simple shared variables inevitably produce race conditions in multi-agent pipelines; the append-only log makes coordination safe without locks or transactions.
