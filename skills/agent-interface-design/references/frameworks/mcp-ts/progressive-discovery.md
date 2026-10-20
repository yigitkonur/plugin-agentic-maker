# Dynamic Tool Lists in TypeScript

> Read when: you are changing the visible tool list at runtime, notifying clients, or handling calls to hidden tools in a TypeScript MCP server.

Explanation and rules: ../../mcp/patterns-dynamic-tool-lists.md

> Version note: SDK method names are as the source states them; verify against the installed SDK (see ../../fresh/mcp-client-and-sdk-quirks.md).

## Pattern 5: Dynamic Tool List Changes Nuke the KV/Prefix Cache

```typescript
// Good: change tools once at session boundaries
server.onRequest("set_mode", (params) => {
  if (params.mode === "admin") enableAdminTools(); // one invalidation
});

// Bad: change tools on every request
server.onRequest("tools/call", (params) => {
  pruneIrrelevantTools(params.context); // cache miss every time
});
```

## Pattern 6: Use `notifications/tools/list_changed` for Dynamic Tooling

`RegisteredTool` mutations send the notification automatically:

```typescript
const tool = server.registerTool("query_db", {
  description: "Run a read-only SQL query",
  inputSchema: { query: z.string() },
}, async ({ query }) => {
  return { content: [{ type: "text", text: await db.query(query) }] };
});

// Each triggers notifications/tools/list_changed automatically:
tool.disable();  // hides from tools/list
tool.enable();   // makes visible again
tool.update({ description: "Read-only SQL (max 1000 rows)" });
tool.remove();   // permanently removes
```

Manual notification:

```typescript
await server.notification({
  method: "notifications/tools/list_changed",
});
```

## Pattern 8: Graceful Fallback for Hidden Tools

Detection and recovery:

```typescript
// Registry of all tools (including currently hidden ones)
const allTools = new Map<string, ToolDefinition>();
const visibleTools = new Set<string>();

// Override the default "tool not found" behavior
server.setToolNotFoundHandler(async (toolName: string, params: unknown) => {
  if (allTools.has(toolName)) {
    // Tool exists but is hidden -- explain and offer the path to unlock it
    const tool = allTools.get(toolName)!;
    return {
      content: [{
        type: "text",
        text: JSON.stringify({
          error: "TOOL_NOT_CURRENTLY_VISIBLE",
          tool_name: toolName,
          message: `"${toolName}" exists but is not active in your current session mode.`,
          how_to_unlock: tool.unlockVia
            ? `Call ${tool.unlockVia} first to activate this tool.`
            : "Contact your administrator to enable this capability.",
          current_alternatives: visibleTools.has("search_tools")
            ? [`Call search_tools to discover available alternatives to ${toolName}.`]
            : [],
        })
      }],
      isError: true,
    };
  }

  // Truly unknown tool
  return {
    content: [{ type: "text", text: `Unknown tool: "${toolName}". Call list_tools to see available tools.` }],
    isError: true,
  };
});
```

On-demand restoration:

```typescript
server.tool("restore_tool", "Restore a temporarily hidden tool for this session", {
  tool_name: z.string(),
  reason: z.string().describe("Why this tool is needed now"),
}, async ({ tool_name, reason }) => {
  if (!allTools.has(tool_name)) {
    return { content: [{ type: "text", text: `"${tool_name}" does not exist.` }], isError: true };
  }
  visibleTools.add(tool_name);
  await server.notifyToolsChanged();
  return { content: [{ type: "text", text: `"${tool_name}" restored for this session.` }] };
});
```
