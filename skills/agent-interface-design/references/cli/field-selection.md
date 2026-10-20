# Field Selection

> Read when: list or get commands return more data than an agent needs and you want to let it request only some fields.

<!-- src: audit-agentic-cli/references/output-contracts.md#5. Field Selection -->
## Field selection flags

Allow agents to request only the fields they need. This keeps output small and parsing cheap.

```bash
# Select specific fields
mycli list resources --json --fields id,name,status

# Use jq expressions
mycli get resource foo --json --jq '.status'

# Combine with other filters
mycli list resources --json --fields id,status --filter "status=active"
```

Rules:

- With `--fields`, keep the same envelope; only the keys inside `result` (or inside each element of `result.items`) are filtered.
- Unknown field names are skipped, not errors, in the reference implementation; a stricter CLI may fail with exit 6 (`validation`). Document which.
- Selecting no fields (empty list) returns the full object.

Implementations: `../frameworks/go/output-contracts.md` and `../frameworks/python/output-contracts.md` (`filterFields`, `filter_fields`).
