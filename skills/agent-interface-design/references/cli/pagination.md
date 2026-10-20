# Pagination

> Read when: a list command can return many results and the agent must walk pages, cursors or `--all` safely.

<!-- src: audit-agentic-cli/references/output-contracts.md#6. Pagination | audit-agentic-cli/references/execution-patterns.md#9. Pagination Patterns | audit-agentic-cli/references/execution-patterns.md#Paginated Response Structure -->
## Response shape

For list operations that may return many results, put the page in `result`:

```json
{
  "ok": true,
  "result": {
    "items": [
      {"id": "res_001", "name": "Resource 1"},
      {"id": "res_002", "name": "Resource 2"}
    ],
    "total": 150,
    "has_more": true,
    "next_cursor": "eyJpZCI6MTIzfQ=="
  },
  "next_command": "mycli list items --per-page 50 --cursor 'eyJpZCI6MTIzfQ=='"
}
```

> Note: use `result.items`, `result.next_cursor`, `result.has_more` and optional `result.total`. Optional offset-mode extras under `result`: `page`, `per_page`, `prev_cursor`, `has_previous`, `total_pages`.

<!-- src: audit-agentic-cli/references/output-contracts.md#Pagination Fields -->
## Fields

| Field | Type | Description |
|-------|------|-------------|
| `items` | array | The page of results |
| `total` | integer | Total number of items (optional; omit if unknown or expensive) |
| `page` | integer | Current page number (1-indexed, offset mode) |
| `per_page` | integer | Items per page |
| `has_more` | boolean | Whether more pages exist |
| `next_cursor` | string | Opaque cursor for next page |

<!-- src: audit-agentic-cli/references/output-contracts.md#CLI Flags | audit-agentic-cli/references/execution-patterns.md#Cursor-Based Pagination -->
## Cursor first, flags

Cursor-based pagination is preferred for large datasets because it is stable under concurrent modification. Fetch one extra row to decide `has_more`.

```bash
# Basic cursor pagination
mycli list items --per-page 50

# Continue with cursor from previous response
mycli list items --per-page 50 --cursor "eyJpZCI6MTAwfQ=="

# Fetch all pages automatically (use with caution)
mycli list items --all --per-page 100

# Specific page (offset-based fallback)
mycli list items --page 3 --per-page 50
```

<!-- src: audit-agentic-cli/references/execution-patterns.md#Pagination Flag Standards -->
## Flag standards

| Flag | Description | Default |
|------|-------------|---------|
| `--per-page <n>` | Items per page | 20-100 |
| `--page <n>` | Page number (1-indexed, offset-based) | 1 |
| `--cursor <token>` | Cursor for next page | None |
| `--all` | Fetch all pages automatically | false |
| `--max-pages <n>` | Maximum pages when using `--all` | 100 |
| `--direction <dir>` | Pagination direction: `forward` \| `backward` | forward |
| `--sort-by <field>` | Sort field | created_at |
| `--sort-order <order>` | Sort order: `asc` \| `desc` | desc |

With `--all`, the CLI walks `next_cursor` until `has_more` is false or `--max-pages` is reached, and returns every item under `result.items`.

Implementations: `../frameworks/go/execution-patterns-paging-rate.md`, `../frameworks/python/execution-patterns-paging-rate.md`, `../frameworks/node/execution-patterns-paging-rate.md`.

<!-- src: audit-agentic-cli/references/output-contracts.md#Pagination Envelope Schema -->
## Pagination fields schema

Validates the pagination fields carried in `result` (Draft-07).

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://schemas.cli-agents.dev/pagination.json",
  "title": "PaginationEnvelope",
  "description": "Pagination metadata for list operations",
  "type": "object",
  "required": ["has_more"],
  "properties": {
    "total": { "type": "integer", "minimum": 0, "description": "Total number of items (omit if unknown/expensive)" },
    "page": { "type": "integer", "minimum": 1, "description": "Current page number (1-indexed)" },
    "per_page": { "type": "integer", "minimum": 1, "maximum": 1000, "description": "Items per page", "default": 20 },
    "has_more": { "type": "boolean", "description": "Whether additional pages exist" },
    "next_cursor": { "type": "string", "description": "Opaque cursor for fetching the next page" },
    "prev_cursor": { "type": "string", "description": "Opaque cursor for fetching the previous page" }
  },
  "additionalProperties": false
}
```
