# Response Formats in TypeScript (YAML and TSV)

> Read when: you are returning YAML or TSV from a TypeScript MCP tool instead of JSON.

Explanation and rules: ../../mcp/responses-formats-and-structured.md

## Pattern 6: Default to YAML Over JSON for LLM-Consumable Responses

Offer a format parameter so the agent can request JSON when it needs programmatic processing.

```typescript
import yaml from "js-yaml";

server.registerTool("get_design_tokens", {
  inputSchema: {
    file_key: z.string(),
    output_format: z.enum(["yaml", "json"]).default("yaml"),
  },
}, async ({ file_key, output_format }) => {
  const result = await fetchDesignTokens(file_key);
  const formatted = output_format === "json"
    ? JSON.stringify(result, null, 2)
    : yaml.dump(result, { lineWidth: -1 });

  return { content: [{ type: "text", text: formatted }] };
});
```

## Pattern 7: Use TSV for Tabular Data to Save 30-40% of Tokens

```typescript
function toTSV(rows: Record<string, unknown>[]): string {
  if (rows.length === 0) return "(no results)";
  const headers = Object.keys(rows[0]);
  const lines = [
    headers.join("\t"),
    ...rows.map(row => headers.map(h => String(row[h] ?? "")).join("\t"))
  ];
  return lines.join("\n");
}

server.registerTool("query_users", {
  inputSchema: {},
}, async () => {
  const users = await db.query(`SELECT name, age, city, role FROM users`);
  return {
    content: [{
      type: "text",
      text: `Found ${users.length} users:\n\n${toTSV(users)}`
    }]
  };
});
```

TSV breaks down with nested objects, arrays within cells, or values containing tabs or newlines. Fall back to YAML or JSON for those.
