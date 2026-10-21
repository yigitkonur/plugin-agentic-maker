# Annotations, structuredContent and Example Responses in TypeScript

> Read when: you are adding content annotations, an `outputSchema` with `structuredContent`, or an example response to a TypeScript MCP tool.

Explanation and rules: ../../mcp/responses-formats-and-structured.md and ../../mcp/responses-steering-and-examples.md

## Pattern 8: Use Content Annotations to Separate User-Facing and Assistant-Facing Data

```typescript
server.registerTool("search_records", {
  inputSchema: { query: z.string() },
}, async ({ query }) => {
  const { results, meta } = await search(query);

  return {
    content: [
      {
        type: "text",
        text: `Found ${results.length} matching records.`,
        annotations: {
          priority: 1.0,
          audience: ["user", "assistant"],
        },
      },
      {
        type: "text",
        text: [
          `Debug: cache_hit=${meta.cacheHit}, latency=${meta.latencyMs}ms`,
          `Query plan: ${meta.queryPlan}`,
          `Filtered: ${meta.filteredCount} by permissions`,
          `Auth token TTL: ${meta.tokenTTL}s`,
        ].join("\n"),
        annotations: {
          priority: 0.3,
          audience: ["assistant"],
        },
      },
    ],
  };
});
```

## Pattern 9: Declare Output Schemas and Return structuredContent

If you declare an `outputSchema`, you must return `structuredContent`. Always return text `content` as well.

```typescript
import { z } from "zod";

server.registerTool("get_weather", {
  description: "Get current weather for a city",
  inputSchema: {
    city: z.string().describe("City name"),
  },
  outputSchema: {
    temperature: z.number().describe("Temperature in Celsius"),
    conditions: z.string().describe("Weather conditions"),
    humidity: z.number().describe("Humidity percentage"),
  },
}, async ({ city }) => {
  const weather = await fetchWeather(city);

  return {
    // Text content for clients that don't support structured output
    content: [{
      type: "text",
      text: `${city}: ${weather.temperature}C, ${weather.conditions}, ${weather.humidity}% humidity`,
    }],
    // Structured content validated against outputSchema
    structuredContent: {
      temperature: weather.temperature,
      conditions: weather.conditions,
      humidity: weather.humidity,
    },
  };
});
```

## Pattern 10: Put Example Responses in Tool Descriptions

Without an example, the agent guesses or wastes a call:

```typescript
server.registerTool("list_users", {
  description: "List users in the workspace",
  inputSchema: { role: z.string().optional() },
}, handler);
```

With an example, the agent knows what to expect:

```typescript
server.registerTool("list_users", {
  description: `List users in the workspace.

Returns a JSON object with:
- "users": array of {id, name, email, role}
- "total": total count (may exceed returned results)
- "has_more": whether more pages exist

Example response:
{
  "users": [
    {"id": "u_abc1", "name": "Jane Doe", "email": "jane@example.com", "role": "admin"},
    {"id": "u_abc2", "name": "Bob Smith", "email": "bob@example.com", "role": "member"}
  ],
  "total": 47,
  "has_more": true
}

Use "page" param to paginate. Pass user "id" values to get_user_details.`,
  inputSchema: {
    role: z.string().optional().describe("Filter by role: admin, member, viewer"),
    page: z.number().optional().describe("Page number, starts at 1"),
  },
}, handler);
```
