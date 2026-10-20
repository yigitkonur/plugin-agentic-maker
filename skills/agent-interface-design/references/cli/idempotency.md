# Idempotency

> Read when: a command may be retried by an agent and must not duplicate or corrupt state.

<!-- src: audit-agentic-cli/references/execution-patterns.md#1. Idempotency Patterns | audit-agentic-cli/references/execution-patterns.md#Verb Semantics -->
## Verb semantics

Idempotent operations produce the same result regardless of how many times they are executed. This is critical for retry logic and agent workflows.

| Verb | Absent Target | Present Target | Retry Safe? |
|------|--------------|----------------|-------------|
| `create` | Create | Fail (conflict) | With idempotency key |
| `apply` | Create | Update/patch | After conflict resolution |
| `ensure` | Create | No-op or update if needed | Yes |
| `delete` | Success (or 404) | Delete | Yes (absent = done) |
| `sync` | Create all | Update to match | Yes |

<!-- src: audit-agentic-cli/references/execution-patterns.md#Idempotency Key Pattern -->
## Idempotency key

```bash
# Same key = same result (server caches outcome)
mycli create resource --idempotency-key "create-foo-v1" --name foo
```

- The key is caller-chosen and stable across retries of the same intent.
- A repeat with the same key returns the cached outcome instead of creating again.
- The reference implementations cache successful results for 24 hours (`24*time.Hour`, `86400`, `24 * 60 * 60 * 1000`).
- Do not cache errors (except for specific cases); a retry after a failure must be able to run the operation again.
- A `create` without a key that hits an existing target fails with exit 5 (`conflict`).

Implementations: `../frameworks/go/execution-patterns-retry.md`, `../frameworks/python/execution-patterns-retry.md`, `../frameworks/node/execution-patterns-retry.md`.

<!-- src: audit-agentic-cli/references/execution-patterns.md#Declarative vs Imperative -->
## Declarative vs imperative

| Style | Example | When to Use |
|-------|---------|-------------|
| **Declarative** | `apply -f config.yaml` | Complex resources, GitOps |
| **Imperative** | `create`, `delete`, `scale` | Simple one-off actions |

Declarative apply: specify the desired state; the tool works out how to get there, and the output shows what changed.

```bash
mycli apply -f deployment.yaml
```
```json
{
  "ok": true,
  "changes": [
    {"action": "update", "resource": "deployment/web", "field": "replicas", "old": 2, "new": 3}
  ]
}
```

Preview the changes before committing with `dry-run.md`.
