---
as_of: 2026-07-04
verify_before_citing: true
---
# Client support for MCP resources, prompts and completions

> Read when: you are about to rely on a client fetching resources, saving prompt arguments, or offering completions, and need to know what was reported.

The source gives no survey date for these remarks; treat each as a practitioner report and test with the target client. Core guidance: `../mcp/protocol-resources.md`, `../mcp/protocol-prompts.md`, `../mcp/protocol-resources-vs-tools.md`. Wider matrix: `client-compatibility.md`.

<!-- src: audit-agentic-mcp/references/patterns/resources-and-prompts.md#1. Use Resources as On-Demand Documentation Referenced in Errors -->
## Automatic resource fetching

- Some clients (Goose was named) fetch a resource automatically when an error message references it; others need the model to request it explicitly.

<!-- src: audit-agentic-mcp/references/patterns/resources-and-prompts.md#2. Use Resource Templates with URI Patterns for Scalable Data Access -->
## Completions for resource templates

- Auto-suggested values for template variables are supported in the VS Code MCP extension and some other clients.

<!-- src: audit-agentic-mcp/references/patterns/resources-and-prompts.md#3. Use MCP Prompts for Repeatable Workflow Entry Points -->
## Prompt support

- Most clients do not fully support persistence of prompt template values.
- Claude Desktop supports prompts but cannot persist saved parameter values across sessions.

<!-- src: audit-agentic-mcp/references/patterns/resources-and-prompts.md#4. When to Use Resources vs Tools -->
## Resource support overall

- Most builders use only tools because client support for resources is inconsistent.
- Resources work well in Goose and some clients; Claude Desktop and Claude Code support is limited.
