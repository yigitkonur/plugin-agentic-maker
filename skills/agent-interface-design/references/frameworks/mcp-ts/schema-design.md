# Schema Coercion and Format Errors in TypeScript

> Read when: you are making Zod input schemas tolerant of LLM-serialized types and giving regex failures a copyable example.

Explanation and rules: ../../mcp/schemas-coercion-and-portability.md

## Pattern 1: Use `z.coerce` and `z.preprocess` for Type Safety

Coerced number:

```typescript
// Breaks when LLM sends "3"
count: z.number().describe("Number of results")

// Handles "3", 3, "3.5" gracefully
count: z.coerce.number().describe("Number of results")
```

Coerced boolean (handles every boolean variant an LLM might send):

```typescript
const coercedBoolean = z.preprocess((val) => {
  if (typeof val === "boolean") return val;
  if (typeof val === "string") {
    if (val.toLowerCase() === "true") return true;
    if (val.toLowerCase() === "false") return false;
  }
  return val;
}, z.boolean());
```

Use it in a tool schema:

```typescript
server.tool("search", {
  query: z.string(),
  includeArchived: coercedBoolean.optional().default(false)
    .describe("Include archived results"),
}, async ({ query, includeArchived }) => {
  // includeArchived is always a real boolean here
});
```

## Pattern 2: Pair Regex Validation with Human-Readable Examples

The LLM never sees the regex, only the error message. Make the message a working example.

```typescript
// Bad: LLM gets "Invalid input" and no idea what format is expected
nodeId: z.string().regex(/^I?\d+[:|-]\d+/)

// Good: LLM gets "Node ID must be like '1234:5678' or 'I5666:180910;1:10515'"
nodeId: z.string()
  .regex(
    /^I?\d+[:|-]\d+/,
    "Node ID must be like '1234:5678' or 'I5666:180910;1:10515'"
  )
```

Apply it to any format constraint:

```typescript
// Hex color
color: z.string()
  .regex(/^#[0-9a-fA-F]{6}$/, "Must be hex color like '#FF5733' or '#00aa99'")

// Semver
version: z.string()
  .regex(/^\d+\.\d+\.\d+$/, "Must be semver like '1.2.3' or '0.10.0'")

// Cron expression
schedule: z.string()
  .regex(/^(\S+\s){4}\S+$/, "Must be cron like '0 9 * * 1' (every Monday 9am)")
```
