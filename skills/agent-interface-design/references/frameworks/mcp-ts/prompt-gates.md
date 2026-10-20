# Prompt Gate Helpers in TypeScript

> Read when: you are emitting state, instructions and next-tool tags from a TypeScript MCP tool response.

Explanation and rules: ../../decisions/steering-contract.md

## Section 3: Build State Machines via Sequential Tool Responses

Server-side helper that renders one gate per response:

```typescript
function buildStateResponse(state: string, data: any,
    instructions: string, nextTool?: string): string {
  return [`<state>${state}</state>`,
    `<instructions>${instructions}</instructions>`,
    `<data>${JSON.stringify(data)}</data>`,
    nextTool ? `<next_tool>${nextTool}</next_tool>` : ""]
    .filter(Boolean).join("\n");
}
```
