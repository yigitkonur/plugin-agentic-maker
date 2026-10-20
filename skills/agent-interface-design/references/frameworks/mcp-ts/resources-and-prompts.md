# TypeScript: resource templates with completion

> Read when: you are registering a templated resource with completions and server-side validation in a TypeScript MCP server.

Core guidance: `../../mcp/protocol-resources.md`.

<!-- src: audit-agentic-mcp/references/patterns/resources-and-prompts.md#2. Use Resource Templates with URI Patterns for Scalable Data Access -->
## Cuisine resource template

```typescript
server.registerResource(
  "recipes",
  new ResourceTemplate("file://recipes/{cuisine}", {
    list: undefined,
    complete: {
      cuisine: (value) => CUISINES.filter(c => c.startsWith(value)),
    },
  }),
  { title: "Cuisine-Specific Recipes", description: "Markdown recipes per cuisine" },
  async (uri, vars) => {
    const cuisine = vars.cuisine as string;
    if (!CUISINES.includes(cuisine)) {
      throw new Error(`Unknown cuisine: ${cuisine}. Valid: ${CUISINES.join(', ')}`);
    }
    return {
      contents: [{
        uri: uri.href,
        mimeType: "text/markdown",
        text: formatRecipesAsMarkdown(cuisine)
      }],
    };
  },
);
```
