# Tool Descriptions in TypeScript

> Read when: you are writing the `instructions` field or enforcing description length in a TypeScript MCP server.

Explanation and rules: ../../mcp/descriptions-structure-and-length.md and ../../mcp/descriptions-schema-split-and-examples.md

## Pattern 9: Use the `instructions` Field as Your Server's skills.md

```typescript
const server = new McpServer({ name: "acme-crm", version: "1.0.0" }, {
  instructions: `
# Acme CRM MCP Server

## Available Capabilities
- Customer management (CRUD + search)
- Invoice lifecycle (create -> send -> pay -> void)
- Activity log queries

## Recommended Workflows
1. **Look up a customer** -> search_customers -> get_customer
2. **Send an invoice** -> create_invoice -> add_line_items -> send_invoice
3. **Check payment status** -> get_invoice -> get_payment

## Important Constraints
- All write operations require a valid session (call authenticate first)
- Invoice sends are irreversible and trigger customer emails
- Rate limit: 60 requests/min across all tools
  `.trim(),
});
```

## Pattern 11: Over-Verbose Descriptions Reduce Tool Call Rate

The 200-token rule: measure description cost before registering.

```typescript
import type { ToolCallback } from "@modelcontextprotocol/sdk/server/mcp.js";

const estimateTokens = (text: string) => Math.ceil(text.length / 4); // rough: ~4 chars per token

function registerWithLengthCheck(name: string, description: string, inputSchema: z.ZodRawShape, handler: ToolCallback<z.ZodRawShape>) {
  const tokens = estimateTokens(description);
  if (tokens > 200) {
    console.warn(`Tool "${name}" description is ${tokens} tokens (limit: 200). Consider trimming.`);
  }
  server.registerTool(name, { description, inputSchema }, handler);
}
```

Optimal format: Verb + Object + Key Constraint.

```
// Too long (320 tokens):
"This tool allows you to search through the repository's codebase using semantic or
keyword-based queries. It supports both exact string matching and fuzzy semantic
search using vector embeddings. The results will include file paths, line numbers,
and surrounding context..."

// Optimal (~35 tokens):
"Search codebase by keyword or semantic query. Returns file paths, line numbers, and
snippets. Use for finding functions, variables, or concepts. Filter by file type or
directory with optional params."
```

What belongs in the schema, not the description: put parameter-level guidance in each parameter's `describe()`.

```typescript
const searchParams = {
  query: z.string().describe("Search term. Supports regex if prefixed with 're:'"),
  file_type: z.string().optional().describe("Filter by extension, e.g. '.ts' or '.py'"),
};
```
