# Resources or tools for data access

> Read when: you are choosing between a resource and a tool for exposing data, or auditing a server that uses one where the other fits better.

<!-- src: audit-agentic-mcp/references/patterns/resources-and-prompts.md#4. When to Use Resources vs Tools -->
## Pick by trigger, mutability and parameters

Resources and tools both give access to data but serve different purposes; the wrong choice wastes tokens or limits functionality.

| Dimension | Resource | Tool |
|-----------|----------|------|
| **Trigger** | User/client-initiated | Model-initiated |
| **Mutability** | Read-only | Can read AND write |
| **Addressing** | URI-based (`file://docs/api.md`) | Name-based (`search_docs`) |
| **Parameters** | Only URI path variables | Full JSON Schema input |
| **Caching** | `lastModified` annotation, subscriptions (no ETags) | Each call is independent |
| **Token cost** | Typically lower (focused data) | Higher (schema in context) |
| **Client support** | Inconsistent across clients | Universal |

Use a resource when:

- the data is read-only and does not change per request;
- the content is reused across multiple tool calls (documentation, config);
- you want URI-addressable content for cross-server references;
- the data is more than 80% read-only (project files, schemas, templates).

Use a tool when:

- the operation has side effects (creates, updates, deletes);
- parameters are complex (filters, pagination, sorting);
- the model needs to decide when to access the data;
- you need arbitrary input validation beyond URI matching.

## Hybrid pattern

Expose data as a resource for browsing by ID (`customers://{customer_id}`) and provide a tool for complex queries (`search_customers(query, status="active", limit=10)`). Code: `../frameworks/mcp-python/resources-and-prompts.md`.

## Portability default

Most builders use only tools because resource support is inconsistent across clients. If portability matters, default to tools and add resources as a nice-to-have. Per-client detail: `../fresh/mcp-resource-prompt-client-support.md`. Docs-as-resource and templates: `protocol-resources.md`.

Sources: MCP community practice on resource templates for API documentation.
