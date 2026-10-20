# Dry-Run Modes

> Read when: a command changes state and the agent must preview the effect before committing.

<!-- src: audit-agentic-cli/references/execution-patterns.md#3. Dry-Run Modes | audit-agentic-cli/references/execution-patterns.md#Client-side vs Server-side -->
## Client-side vs server-side

| Mode | What It Does | Accuracy |
|------|--------------|----------|
| `--dry-run=client` | Local validation only | May miss server-side issues |
| `--dry-run=server` | Full server processing, no persistence | High accuracy |

Always prefer server-side dry-run when available. A bare `--dry-run` previews and persists nothing. Every destructive command offers `--dry-run`, `--yes` or both (`checks.md`).

<!-- src: audit-agentic-cli/references/execution-patterns.md#Diff Output -->
## Diff output

```bash
$ mycli apply -f config.yaml --dry-run
```

Human-friendly output (stderr or a terminal, never mixed into `--json` stdout):

```
Dry run - no changes will be made

deployment/web
  ~ replicas: 2 → 3

deployment/api
  + (will be created)

configmap/legacy
  - (will be deleted)

Summary: 1 to create, 1 to update, 1 to delete
```

<!-- src: audit-agentic-cli/references/execution-patterns.md#Structured Dry-Run Response -->
## Structured dry-run response

```json
{
  "ok": true,
  "dry_run": true,
  "changes": [
    { "action": "create", "resource_type": "deployment", "resource_id": "web", "diff": null },
    {
      "action": "update",
      "resource_type": "deployment",
      "resource_id": "api",
      "diff": {
        "replicas": {"old": 2, "new": 3},
        "image": {"old": "app:v1.0", "new": "app:v1.1"}
      }
    },
    { "action": "delete", "resource_type": "configmap", "resource_id": "legacy", "diff": null }
  ],
  "summary": { "create": 1, "update": 1, "delete": 1, "unchanged": 5 },
  "validation_warnings": [
    {
      "resource": "deployment/api",
      "message": "Deprecated API version v1beta1, consider upgrading to v1"
    }
  ]
}
```

`action` is one of `create`, `update`, `delete`; `diff` is `null` for create and delete. `dry_run: true` is always present so an agent cannot mistake a preview for an applied change.

Implementations: `../frameworks/go/execution-patterns-safety.md`, `../frameworks/python/execution-patterns-safety.md`.
