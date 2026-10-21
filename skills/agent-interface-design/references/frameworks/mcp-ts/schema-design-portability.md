# Tool Name Safety and Schema Portability in TypeScript

> Read when: you are adding a CI/registration check for tool names or a portability check for input schemas in a TypeScript MCP server.

Explanation and rules: ../../mcp/schemas-coercion-and-portability.md

## Pattern 7: Safe Tool Name Characters Only

Naming convention:

```typescript
// DANGEROUS: will crash some clients
const badNames = [
  "read/file",
  "git-status",
  "search.files",
  "get_user's_data",
];

// SAFE: [a-z0-9_] only, underscore_separated
const goodNames = [
  "read_file",
  "git_status",
  "search_files",
  "get_user_data",
];
```

Lint rule:

```typescript
import type { ToolCallback } from "@modelcontextprotocol/sdk/server/mcp.js";

const SAFE_TOOL_NAME = /^[a-z][a-z0-9_]{0,63}$/;

function registerTool(name: string, config: { description?: string; inputSchema?: z.ZodRawShape }, cb: ToolCallback<z.ZodRawShape>) {
  if (!SAFE_TOOL_NAME.test(name)) {
    throw new Error(
      `Invalid tool name "${name}". Use only lowercase letters, digits, and underscores. ` +
      `Must start with a letter. Max 64 characters.`
    );
  }
  server.registerTool(name, config, cb);
}
```

Add this check to CI to catch violations before deployment.

## Pattern 8: Cross-Model Portable Schema Rules

The 7 rules as code comments:

```typescript
// Rule 1: No oneOf / anyOf / allOf -- Gemini ignores tools with these
// Bad
const bad = { oneOf: [{ type: "string" }, { type: "number" }] };
// Good -- pick the most permissive type, coerce server-side
const good = { type: "string", description: "Can also be a number (will be converted)" };

// Rule 2: Max 3 levels of nesting -- GPT-4 degrades beyond this

// Rule 3: No $ref -- most clients don't resolve references in tool schemas
// Inline all definitions

// Rule 4: No format validators beyond date-time and email -- inconsistently supported
// Bad: { type: "string", format: "uri" }  -- GPT-4 ignores format
// Good: describe the format in the description field instead

// Rule 5: No default for required fields -- confuses some model implementations
// Only apply defaults to optional fields

// Rule 6: Keep enums under 10 values -- larger enums reduce model accuracy
// Split large enums into a separate "mode" tool that narrows the scope

// Rule 7: Use additionalProperties: false -- helps all models understand the schema is strict
```

Quick cross-model schema validator:

```typescript
type JsonSchema = Record<string, any>;
declare function countNestingDepth(schema: JsonSchema): number; // walk properties/items, return max depth

function validatePortability(schema: JsonSchema): string[] {
  const issues: string[] = [];
  if (schema.oneOf || schema.anyOf || schema.allOf) issues.push("Remove oneOf/anyOf/allOf for Gemini compatibility");
  if (schema.$ref) issues.push("Inline $ref for cross-client compatibility");
  if (countNestingDepth(schema) > 3) issues.push("Nesting too deep (>3) for GPT-4 reliability");
  if (Array.isArray(schema.enum) && schema.enum.length >= 10) issues.push("Large enum (10+) degrades accuracy");
  return issues;
}
```
