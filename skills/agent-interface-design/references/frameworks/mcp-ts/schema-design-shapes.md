# Schema Shapes in TypeScript

> Read when: you are flattening a nested Zod schema, replacing a union, describing enums, or splitting a tool with too many parameters.

Explanation and rules: ../../mcp/schemas-flat-and-sized.md

## Pattern 3: Keep Schemas Flat, Under 6 Parameters

```typescript
// Nested: LLMs struggle with this structure
server.tool("search", {
  query: z.string(),
  filters: z.object({
    dateRange: z.object({
      start: z.string(),
      end: z.string(),
    }),
    status: z.enum(["active", "archived"]),
    tags: z.array(z.string()),
  }),
});

// Flat: same capability, much higher accuracy
server.tool("search", {
  query: z.string(),
  startDate: z.string().optional().describe("Start date (ISO 8601)"),
  endDate: z.string().optional().describe("End date (ISO 8601)"),
  status: z.enum(["active", "archived"]).optional(),
  tags: z.string().optional().describe("Comma-separated tags"),
});
```

## Pattern 4: Accept Flexible Formats, Normalize Server-Side

```typescript
// Bad: LLMs frequently mishandle union types
date: z.union([
  z.string().datetime(),
  z.number().describe("Unix timestamp"),
  z.enum(["today", "yesterday", "last_week"]),
])

// Good: higher accuracy, let the LLM express naturally
date: z.string().describe(
  "Date in any format: ISO 8601, Unix timestamp, or relative ('yesterday', 'last week')"
)
```

Normalize in the handler:

```typescript
import { parseDate } from "chrono-node"; // or your preferred parser

async function handler({ date }: { date: string }) {
  const parsed = parseDate(date) ?? new Date(date);
  if (!parsed || isNaN(parsed.getTime())) {
    return { content: [{ type: "text", text: "Could not parse date. Try ISO 8601 like '2024-01-15'." }] };
  }
  // Use `parsed` -- it's always a valid Date
}
```

## Pattern 5: Describe Each Enum Value Inline

```typescript
// Bad: LLM knows the options but not when to use each
livecrawl: z.enum(["fallback", "preferred"])

// Good: LLM understands the semantics of each option
livecrawl: z.enum(["fallback", "preferred"]).describe(
  "Live crawl mode - 'fallback': use live crawling as backup if cached " +
  "version is unavailable, 'preferred': always prioritize live crawling " +
  "over cache (default: 'fallback')"
)

// Log level with behavior descriptions
level: z.enum(["error", "warn", "info", "debug"]).describe(
  "'error': only critical failures, 'warn': errors + potential issues, " +
  "'info': general operational events, 'debug': verbose output for troubleshooting"
)

// Output format with use-case guidance
format: z.enum(["json", "csv", "markdown"]).describe(
  "'json': structured data for programmatic use, 'csv': tabular data " +
  "for spreadsheets, 'markdown': human-readable formatted output"
)
```

## Pattern 6: Break Tools Over 40 Parameters

Strategy 1: split by workflow stage.

```typescript
// One tool with 30+ params
server.tool("deploy", { env, region, scaling, healthCheck, rollback, ... })

// Three focused tools
server.tool("deploy_configure", {
  env: z.enum(["staging", "production"]),
  region: z.string(),
});
server.tool("deploy_execute", {
  configId: z.string().describe("ID from deploy_configure"),
  strategy: z.enum(["rolling", "blue-green"]),
});
server.tool("deploy_verify", {
  deploymentId: z.string().describe("ID from deploy_execute"),
});
```

Strategy 2: action-routed facade.

```typescript
server.tool("database", {
  action: z.enum(["query", "insert", "schema"]),
  table: z.string(),
  where: z.string().optional().describe("Only for 'query'"),
  data: z.string().optional().describe("Only for 'insert'"),
});
```
