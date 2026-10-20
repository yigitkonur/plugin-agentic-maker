# Dynamic Tool Lists in TypeScript

> Read when: you are changing the visible tool list at runtime, notifying clients, or handling calls to hidden tools in a TypeScript MCP server.

Explanation and rules: ../../mcp/patterns-dynamic-tool-lists.md

> Version note: SDK method names are as the source states them; verify against the installed SDK (see ../../fresh/mcp-client-and-sdk-quirks.md).

## Pattern 5: Dynamic Tool List Changes Nuke the KV/Prefix Cache

```typescript
// Good: change tools once, at a session boundary, from a tool the agent calls on purpose
server.registerTool("set_mode", {
  description: "Switch the session mode.",
  inputSchema: { mode: z.enum(["standard", "admin"]) },
}, async ({ mode }) => {
  if (mode === "admin") adminTools.forEach((t) => t.enable()); // one list_changed, one cache invalidation
  return { content: [{ type: "text", text: `Mode: ${mode}` }] };
});

// Bad: change the list while serving ordinary calls
server.registerTool("search", { description: "Search.", inputSchema: { query: z.string() } }, async (args) => {
  pruneIrrelevantTools(args); // a list_changed and a cache miss on every call
  return runSearch(args);
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
await server.sendToolListChanged(); // McpServer; low-level: server.server.notification({ method: "notifications/tools/list_changed" })
```

## Pattern 8: Graceful Fallback for Hidden Tools

Detection and recovery. The SDK has no "tool not found" hook: a call to a hidden or unknown tool fails with a protocol error the agent cannot act on. So keep one always-visible tool that explains, name it in the server `instructions`, and hide tools with `disable()` rather than by not registering them:

```typescript
import type { RegisteredTool } from "@modelcontextprotocol/sdk/server/mcp.js";

// Every tool is registered once; hidden ones are disabled (not listed, calls rejected)
const registered = new Map<string, RegisteredTool>();
const hidden = new Map<string, { unlockVia?: string }>(); // name -> how to unlock it
registered.get("export_all")?.disable();
hidden.set("export_all", { unlockVia: "restore_tool" });

server.registerTool("explain_tool", {
  description: "Explain why a tool is unavailable and how to unlock it.",
  inputSchema: { tool_name: z.string() },
}, async ({ tool_name }) => {
  const info = hidden.get(tool_name);
  if (!info) {
    return { content: [{ type: "text", text: `Unknown tool: "${tool_name}". Call tools/list to see the available tools.` }], isError: true };
  }
  return {
    content: [{ type: "text", text: JSON.stringify({
      error: "TOOL_NOT_CURRENTLY_VISIBLE",
      tool_name,
      message: `"${tool_name}" exists but is not active in your current session mode.`,
      how_to_unlock: info.unlockVia
        ? `Call ${info.unlockVia} first to activate this tool.`
        : "Ask an administrator to enable this capability.",
    }) }],
    isError: true,
  };
});
```

On-demand restoration:

```typescript
server.registerTool("restore_tool", {
  description: "Restore a temporarily hidden tool for this session.",
  inputSchema: { tool_name: z.string(), reason: z.string().describe("Why this tool is needed now") },
}, async ({ tool_name, reason }) => {
  const tool = registered.get(tool_name);
  if (!tool) {
    return { content: [{ type: "text", text: `"${tool_name}" does not exist.` }], isError: true };
  }
  tool.enable(); // the SDK sends notifications/tools/list_changed itself
  hidden.delete(tool_name);
  return { content: [{ type: "text", text: `"${tool_name}" restored for this session.` }] };
});
```
