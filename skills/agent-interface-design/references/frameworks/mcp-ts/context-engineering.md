# Context Budget Helpers in TypeScript

> Read when: you are trimming tool definitions, cleaning CLI output, paginating or truncating responses, or capping the active tool set in TypeScript.

Explanation and rules: ../../mcp/budget-tool-definitions.md and ../../mcp/budget-response-size.md

## Pattern 1: Tool Descriptions Eat ~15% of Your Context Budget

```typescript
// Bad -- 140+ tokens for this one tool
server.tool(
  "search_documents",
  {
    description: "Searches through all documents in the repository using full-text search. " +
      "Supports boolean operators, phrase matching, and field-specific queries. " +
      "Returns paginated results with relevance scores and highlighted snippets.",
    inputSchema: { /* ... */ }
  }
);

// Good -- under 100 tokens, same capability
server.tool(
  "search_documents",
  {
    description: "Full-text search across repo docs. Supports boolean, phrase, field queries. Returns paginated results.",
    inputSchema: { /* ... */ }
  }
);
```

Audit your tool token budget before registering:

```typescript
function estimateToolTokens(tools: Tool[]): void {
  for (const tool of tools) {
    const raw = JSON.stringify(tool);
    const estimate = Math.ceil(raw.length / 4); // rough chars-to-tokens
    if (estimate > 100) {
      console.warn(`[token-audit] ${tool.name}: ~${estimate} tokens -- consider trimming`);
    }
  }
}
```

## Pattern 4: Strip ANSI Codes and Progress Bars Before Returning CLI Output

TypeScript equivalent, for Node-based MCP servers:

```typescript
const ANSI_RE = /\x1b\[[0-9;]*[mGKHFJK]/g;
const CR_RE   = /[^\n]*\r/g;

function cleanOutput(raw: string): string {
  return raw.replace(ANSI_RE, '').replace(CR_RE, '').replace(/\n{3,}/g, '\n\n').trim();
}
```

## Pattern 5: Use the Right Data Delivery Strategy for Each Tool Type

Hybrid first-page-plus-summary:

```typescript
interface PaginatedResponse<T> {
  results:       T[];
  total_results: number;
  page:          number;
  total_pages:   number;
  has_more:      boolean;
  hint?:         string;   // only included when has_more === true
}

function paginateResults<T>(
  items:    T[],
  page:     number = 1,
  pageSize: number = 20,
): PaginatedResponse<T> {
  const total_pages = Math.ceil(items.length / pageSize);
  const start  = (page - 1) * pageSize;
  const slice  = items.slice(start, start + pageSize);
  const has_more = page < total_pages;

  return {
    results:       slice,
    total_results: items.length,
    page,
    total_pages,
    has_more,
    ...(has_more && {
      hint: `Showing ${slice.length} of ${items.length}. Use page=${page + 1} for more.`,
    }),
  };
}

// Truncation helper -- always tell the model what was cut
function truncateWithSignal(text: string, maxChars = 8000): string {
  if (text.length <= maxChars) return text;
  const dropped = text.length - maxChars;
  return text.slice(0, maxChars) +
    `\n\n[...truncated — ${dropped} chars omitted. Use a narrower query for more.]`;
}
```

## Pattern 6: Each LLM Has a Tool Limit Beyond Which Accuracy Collapses

The `perModelLimit` values are illustrative; current per-model figures are in ../../fresh/mcp-model-behavior.md.

```typescript
// Tool group registry -- expose only tools relevant to the current task
const TOOL_GROUPS: Record<string, string[]> = {
  "code-review":   ["read_file", "search_code", "get_diff", "add_comment"],
  "deployment":    ["run_pipeline", "get_logs", "rollback", "set_env"],
  "data-analysis": ["query_db", "export_csv", "run_notebook", "plot_chart"],
};

function getToolsForTask(allTools: Map<string, Tool>, hint: string): Tool[] {
  for (const [group, names] of Object.entries(TOOL_GROUPS)) {
    if (hint.toLowerCase().includes(group.replace("-", " "))) {
      return names.map(n => allTools.get(n)!).filter(Boolean);
    }
  }
  return [...allTools.values()].slice(0, 20); // safe universal cap
}

// Progressive disclosure -- start with 3 always-on tools, expand on request
const ALWAYS_ON = ["help", "search", "read_file"];
const perModelLimit: Record<string, number> = { claude: 30, "gpt-4": 20, gemini: 10 };

function enableTool(active: string[], model: string, name: string): boolean {
  const limit = perModelLimit[model] ?? 20;
  if (active.length >= limit || active.includes(name)) return false;
  active.push(name);
  return true;
}
```
