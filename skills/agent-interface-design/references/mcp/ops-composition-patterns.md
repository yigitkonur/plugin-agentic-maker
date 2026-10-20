# Compose MCP servers around one domain each

> Read when: you are deciding how to split functionality across MCP servers, wrap a large API, or generate tools from an OpenAPI spec.

<!-- src: audit-agentic-mcp/references/patterns/composition.md#Composition Patterns -->
Seven composition patterns exist for combining multiple MCP servers, building gateways and creating composable server architectures. This file covers the four that shape the servers themselves (one domain per server, one tool plus resources, provider and transform layers, OpenAPI generation); the gateway, proxy and policy patterns are in `ops-gateway.md`. Code: `../frameworks/mcp-python/composition.md` and `../frameworks/mcp-ts/composition.md`.

<!-- src: audit-agentic-mcp/references/patterns/composition.md#2. Design Composable Servers That the LLM Orchestrates -->
## One domain per server, the model orchestrates

Each MCP server specializes in one domain. Let the LLM orchestrate multi-server workflows: it reasons about workflow sequencing better than any hardcoded router.

Worked example, threat modeling:

```
User: "Analyze the security of our new payment API"

Model orchestration:
1. Calls github_analyze(repo_url)  -> code structure, dependencies
2. Calls threat_framework(app_description=<description from step 1>)  -> STRIDE analysis scaffold
3. Uses the STRIDE data to generate a threat report
4. Calls create_jira_tickets(threats=<identified threats>)  -> tracking tickets
```

Server 1 (`github_analyze`) returns a `description` ("Payment processing API using Express.js with Stripe integration"), `dependencies`, `identified_components` (`auth`, `payment`, `webhook_handler`) and a `next_steps` hint naming `threat_framework()`. Server 2 (`threat_framework`) returns `stride_categories`, a `context_analysis`, a `report_template` and `data_for_report` (raw data for the model to assemble). Python versions: `../frameworks/mcp-python/composition.md`.

Four principles:

1. Each server exposes **data and scaffolds**, not finished outputs.
2. Responses include `next_steps` that reference tools from OTHER servers.
3. Return data in formats other tools can consume as input.
4. Do not make servers depend on each other directly; let the model chain them.

Guidance in tool output (`next_steps`) is the strongest steering lever and the same channel is an attack surface; bound it with namespaced guidance plus an `allowed_next_tools` list, see `../decisions/steering-contract.md`.

Sources: Matt Adams (MCP design principles); r/mcp community discussion.

<!-- src: audit-agentic-mcp/references/patterns/composition.md#3. Wrap Complex APIs in One Tool + Resource Documentation -->
## Wrap a large API in one tool plus resource documentation

For an API with 30+ endpoints, expose a single flexible tool (`api_call(client, method, params)`) and use MCP resources to document it on demand. The tool count stays at 1 while the full API surface remains reachable. Resource URI scheme:

| URI | Content |
|---|---|
| `tool://all` | All available API clients and their methods |
| `tool://{client}/{method}` | Detailed documentation for one method |
| `tool://{client}/{method}/{parameter}` | Detailed docs for one parameter of a method |

The interaction flow:

1. The model calls `api_call` with a guess at the method.
2. If wrong, the error response says "See tool://all for available methods".
3. The model reads the resource to discover the correct method name.
4. The model reads `tool://{client}/{method}` for parameter documentation.
5. The model calls `api_call` correctly.

Resources are not pushed into context preemptively. The model reads them on demand, so a seldom-used method with complex documentation costs no tokens until it is needed.

**Trade-off:** this requires clients that support resource reading, and not all do. Test with your target client; see `../fresh/client-compatibility.md`. Code: `../frameworks/mcp-python/composition.md`.

Sources: r/mcp community discussion.

<!-- src: audit-agentic-mcp/references/patterns/composition.md#4. Use the Provider + Transform Architecture for Maximum Flexibility -->
## Provider and transform layers

A composable server architecture separates where components come from (providers) from how their behavior is modified (transforms). Product names and versions: `../fresh/mcp-gateway-tools.md`.

| Concept | Description | Example |
|---------|-------------|---------|
| **Component** | Atomic unit (Tool, Resource, Prompt) | A `search_contacts` tool |
| **Provider** | Sources components from anywhere | Decorators, filesystem, OpenAPI spec, remote MCP |
| **Transform** | Modifies Provider behavior | Rename, namespace, filter, gate, version |
| **Composition** | Combine Providers + Transforms | Mount sub-servers, proxy remote tools |

Provider types: local functions, a directory of source files (optionally hot-reloaded), an OpenAPI spec, a remote MCP server, and instruction files (skills). Transform examples: namespace all tools from a provider (tools become `github_create_pr`, `github_list_repos`), filter by version (`select="latest"`), gate by authentication (tags plus scopes), rename for consistency.

**The Playbook pattern** composes Providers, Visibility, Auth and Session State into multi-step workflows:

1. The user authenticates.
2. `unlock_admin_mode` updates session state.
3. Admin tools become visible (Visibility Transform).
4. Subsequent calls use the newly available tools.

This replaces ad-hoc glue code with declarative primitives. Python API code: `../frameworks/mcp-python/composition.md`.

Sources: FastMCP 3.0 announcement.

<!-- src: audit-agentic-mcp/references/patterns/composition.md#5. Generate MCP Servers from OpenAPI Specs -->
## Generate tools from an OpenAPI spec

If you already have a well-documented REST API with an OpenAPI spec, you do not need to hand-code each MCP tool: generate them. A proxy loads the spec and translates MCP tool calls into HTTP requests (`tool("createPage", {...})` becomes `POST /v1/pages {...}`, returning a structured MCP response). A public example is Notion's MCP server (see `../fresh/mcp-gateway-tools.md`). Code: `../frameworks/mcp-ts/composition.md`.

When to use this:

- You have 20+ API endpoints and writing individual tools is tedious.
- Your OpenAPI spec is accurate and well maintained.
- You want quick MCP access while iterating on the API itself.

Caveats:

- Auto-generated descriptions inherit whatever is in the spec, often too terse or too technical for model consumption.
- One-to-one endpoint mapping creates tool sprawl. Consolidate related endpoints, for example merge `GET /users/{id}`, `PATCH /users/{id}` and `DELETE /users/{id}` into a single `manage_user` tool.
- Missing: semantic grouping, smart defaults and context-aware parameter descriptions.

Recommended approach: use the proxy as a starting point, then iteratively refine the highest-traffic tools with hand-crafted descriptions through an override (for example `search_pages` described as "Search Notion pages by title or content. Returns page IDs and titles.", with `query` and `limit` (default 10, max 100) parameter descriptions). See `descriptions-structure-and-length.md` for description length.

Sources: Notion MCP server repository.
