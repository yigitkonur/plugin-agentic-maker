# MCP model-portability code snippets (TypeScript, Python)

> Read when: you implement a rule from `fresh/model-behavior-rules-*.md` and need the code shape (Zod unions, Claude cache block, portability test, response cap).

## Rule 2: Zod `union` breaks Gemini, `discriminatedUnion` emits `oneOf`

```typescript
// Breaks on Gemini: z.union emits anyOf
const input = z.object({
  target: z.union([
    z.object({ kind: z.literal("user"), userId: z.string() }),
    z.object({ kind: z.literal("team"), teamId: z.string() }),
  ]),
});

// oneOf is fine for OpenAI-strict and DeepSeek, but Gemini ignores oneOf/anyOf/allOf too
const input = z.object({
  target: z.discriminatedUnion("kind", [
    z.object({ kind: z.literal("user"), userId: z.string() }),
    z.object({ kind: z.literal("team"), teamId: z.string() }),
  ]),
});

// Portable on Gemini: one flat object, an enum, optional fields checked server-side
const flat = z.object({
  kind: z.enum(["user", "team"]),
  userId: z.string().optional(),
  teamId: z.string().optional(),
});
```

This sits against the core stance (avoid `oneOf`/`anyOf` at the top of an input schema; prefer an `action` enum). Ship the union only on an OpenAI-strict or DeepSeek path; use the flat form for Gemini.

## Rule 3: cache the tool-definitions block for 1h (Claude)

```python
# Cache prefix order is tools, then system, then messages. A cache_control mark on
# the last tool caches the whole tool-definitions block; system stays top-level.
request = {
  "tools": [*TOOLS[:-1],
            {**TOOLS[-1], "cache_control": {"type": "ephemeral", "ttl": "1h"}}],
  "system": SYSTEM_PROMPT,
  "messages": [],  # per-request messages
}
```

## Rule 6: cross-client schema portability test

```typescript
function validateCrossClientSchema(schema: any): string[] {
  const issues: string[] = [];
  if (schema.anyOf) issues.push("anyOf: breaks Gemini, Mistral, Llama 4");
  if (schema.$ref) issues.push("$ref: breaks Gemini, Mistral, Qwen 3");
  // countNestingDepth: your own helper that walks properties/items
  if (countNestingDepth(schema) > 3) issues.push("nesting >3: breaks Gemini");
  if (Array.isArray(schema.enum) && schema.enum.length > 20)
    issues.push("enum >20: degrades all non-Claude models");
  return issues;
}
```

The `enum > 20` check is a model-specific report; the core threshold is 10 inline values (see `fresh/model-behavior.md`, Conflicts).

## Rule 7: hard-cap and paginate a tool response

```python
MAX_TOKENS = 25_000   # matches Claude Code default
DEFAULT_PAGE_SIZE = 50

def list_records(filters: dict, offset: int = 0, limit: int = DEFAULT_PAGE_SIZE):
    rows = db.query(filters, offset=offset, limit=limit)
    has_more = len(rows) == limit
    body = render(rows)
    truncated = False
    while approx_tokens(body) > MAX_TOKENS and len(rows) > 1:
        rows, has_more, truncated = rows[:len(rows) // 2], True, True  # halve until under the cap
        body = render(rows)
    return {"rows": body, "has_more": has_more,
            "next_cursor": offset + len(rows) if has_more else None,
            "meta": {"truncated": truncated},
            "next_step": f"Call list_records(offset={offset + len(rows)}) for more."}
```
