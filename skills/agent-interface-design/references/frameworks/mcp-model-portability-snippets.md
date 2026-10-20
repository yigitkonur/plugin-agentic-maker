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

// Works on Gemini: discriminatedUnion emits oneOf
const input = z.object({
  target: z.discriminatedUnion("kind", [
    z.object({ kind: z.literal("user"), userId: z.string() }),
    z.object({ kind: z.literal("team"), teamId: z.string() }),
  ]),
});
```

This sits against the core stance (avoid `oneOf`/`anyOf` at the top of an input schema; prefer an `action` enum). Use it only when you must ship a union to Gemini.

## Rule 3: cache the tool-definitions block for 1h (Claude)

```python
# Put tool definitions in one cached block at the top of the system/tools payload.
messages = [
  {"role": "system", "content": [
    {"type": "text", "text": SYSTEM_PROMPT},
    {"type": "text", "text": TOOL_DEFINITIONS,
     "cache_control": {"type": "ephemeral", "ttl": "1h"}},
  ]},
  # ...then per-request messages
]
```

## Rule 6: cross-client schema portability test

```typescript
function validateCrossClientSchema(schema: any): string[] {
  const issues: string[] = [];
  if (schema.anyOf) issues.push("anyOf: breaks Gemini, Mistral, Llama 4");
  if (schema.$ref) issues.push("$ref: breaks Gemini, Mistral, Qwen 3");
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

def list_records(filters: dict, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE):
    rows = db.query(filters, offset=(page-1)*page_size, limit=page_size)
    body = render(rows)
    if approx_tokens(body) > MAX_TOKENS:
        body = render(rows[:page_size // 2])
    return {"page": page, "rows": body,
            "has_more": len(rows) == page_size,
            "next_step": f"Call list_records(page={page+1}) for more."}
```
