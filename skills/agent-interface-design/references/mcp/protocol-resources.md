# Resources as on-demand docs and scalable data access

> Read when: you are deciding whether to expose documentation or read-only data as MCP resources, or auditing a server whose tool descriptions are bloated with usage detail.

<!-- src: audit-agentic-mcp/references/patterns/resources-and-prompts.md#Resources and Prompts -->
Resources are URI-addressable, read-only data; prompts are user-triggered workflow templates (see `protocol-prompts.md`). Together with tools they cut token waste, give on-demand documentation and create repeatable workflow entry points. Whether to pick a resource or a tool is in `protocol-resources-vs-tools.md`. Code: `../frameworks/mcp-python/resources-and-prompts.md`, `../frameworks/mcp-ts/resources-and-prompts.md`. Client behaviour: `../fresh/mcp-resource-prompt-client-support.md`.

<!-- src: audit-agentic-mcp/references/patterns/resources-and-prompts.md#1. Use Resources as On-Demand Documentation Referenced in Errors -->
## Expose tool documentation as a resource and cite it in errors

Put the full tool documentation in a resource (for example `docs://tools`) and keep each tool description short, ending with a pointer such as "See docs://tools for detailed usage." When a call fails, the error message names the same resource. The model fetches the docs only when it needs help, so the initial context stays lean.

How it plays out:

1. Initial context holds only the brief tool descriptions.
2. The model calls the tool correctly about 90% of the time with just the description.
3. On failure, the error message references `docs://tools`.
4. The model (or client) fetches the resource for detailed guidance.
5. Armed with the full docs, the model retries successfully.

Example error: "Query cannot be empty. See docs://tools for usage examples and valid query formats." with `isError: true`.

Practitioner validation: tool documentation in a markdown file exposed as a resource, plus "see docs://tools for more information" in error messages, made models use the tools correctly more often; the same pattern also worked for syntax-error recovery.

Not every client fetches resources automatically; some need the model to request it explicitly. Test with the target client (see the fresh file above), and keep the error message self-sufficient for the minimum fix.

<!-- src: audit-agentic-mcp/references/patterns/resources-and-prompts.md#2. Use Resource Templates with URI Patterns for Scalable Data Access -->
## Use resource templates instead of one resource per variant

One template definition serves hundreds of variants. A template such as `file://recipes/{cuisine}` resolves dynamically, so Italian, Japanese, Mexican and the rest need no separate registrations.

- **URI pattern matching:** `file://recipes/{cuisine}` resolves on read.
- **Completions:** auto-suggest valid values as the user types (see `protocol-roots-and-completion.md`; client support varies).
- **Server-side validation:** reject invalid values with a clear error that lists the valid ones ("Unknown cuisine: X. Valid: a, b, c").
- **Single definition:** returns `contents` with `uri`, `mimeType` (for example `text/markdown`) and `text`.

Resources beat tools for data access when:

- the data is read-only and changes infrequently;
- the same data is referenced by multiple tools or prompts;
- the data benefits from caching (resources support ETags);
- you want URI-addressable content for cross-server referencing.

Use a tool instead when the read has parameters beyond a URI path: complex filters, pagination, sorting.

Sources: MCP specification (resources), MCP resource-template documentation.
