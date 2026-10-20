# Progressive discovery for large tool catalogs

> Read when: an MCP server exposes about 40 or more tools (or its tools/list is too large) and you need meta-tools, semantic search or staged disclosure.

<!-- src: audit-agentic-mcp/references/patterns/progressive-discovery.md#Progressive Discovery Patterns -->
Patterns for managing large catalogs and reducing context pressure. Cue: up to 20 active tools is the comfortable default, about 30 a warning, 40 or more needs progressive discovery (`../decisions/tool-count.md`). Hiding and revealing tools at runtime, with its cache cost: `patterns-dynamic-tool-lists.md`. Code: `../frameworks/mcp-python/progressive-discovery.md`. Measured token tables: `../fresh/mcp-token-benchmarks.md`.

<!-- src: audit-agentic-mcp/references/patterns/progressive-discovery.md#1. Use Meta-Tools for Large Tool Catalogs (list/describe/execute) -->
## Meta-tools: list, describe, execute

Above about 40 tools, loading every schema into the prompt becomes prohibitively expensive. Replace static exposure with three meta-tools:
- `list_tools(prefix="/")`: list categories or tools matching a prefix, for example `list_tools('/hubspot/deals/')` returns deal-related tools.
- `describe_tools(tool_id)`: the full input schema for one tool; "Call this before execute_tool to understand required parameters."
- `execute_tool(tool_id, arguments)`: run a tool by ID; "Call describe_tools first to get the correct schema."

Impact: the static approach grows with catalog size (tens of thousands of tokens at 40 tools, hundreds of thousands at 400) while the meta-tool approach stays near 1.5-2.5k tokens regardless of count (table in the fresh file).

Critical design details:
- **Separate schema retrieval from discovery.** `list_tools` returns only names; `describe_tools` returns the full schema, so 100 schemas are not sent when the model needs one.
- **Use hierarchical prefixes** in tool IDs: `/hubspot/deals/create`, `/hubspot/contacts/search`, so `list_tools` queries are precise.
- The initial context holds only about 1.5-2.5k tokens regardless of total tool count.

Anti-pattern: loading all schemas statically; beyond a few hundred tools the catalog no longer fits in the model's context window and tasks cannot complete at all (limit figures: fresh file).

<!-- src: audit-agentic-mcp/references/patterns/progressive-discovery.md#2. Use Semantic Search with Embeddings for 100+ Tools -->
## Semantic search for 100+ tools

For very large catalogs, replace hierarchical navigation with one `find_tools(query)` meta-tool that uses embedding similarity over `name: description` text to return the top matches (the example returns `id`, `name`, `description` for the top 5; example query: `find_tools('list recent HubSpot deals')`).

Semantic vs progressive:
- **Semantic:** faster for simple, single-intent queries; about 1.3k initial tokens plus about 3k per task.
- **Progressive (meta-tools):** better for complex multi-step workflows where the agent needs full visibility of available actions; about 2.5k initial plus about 2.5k per task.

Implementation tips:
- Pre-compute embeddings offline; only query the index at runtime.
- Cache recent query-to-tool mappings for 5-10 minutes.
- Store embeddings in FAISS (in-memory) or Pinecone (distributed).
- Keep full JSON schemas in a separate KV store, not in the embedding index.

<!-- src: audit-agentic-mcp/references/patterns/progressive-discovery.md#4. Four-Stage Progressive Disclosure Pattern -->
## Four-stage progressive disclosure

Stage-wise exposure mirrors how a human explores an unfamiliar system; each stage returns minimal data.

```
1. discover_categories()
   -> ["GitHub", "Slack", "Database", "CRM"]
2. get_category_actions("GitHub")
   -> [{"name": "create_pr", "summary": "Create a pull request"},
       {"name": "search_repos", "summary": "Search repositories"},
       {"name": "list_issues", "summary": "List issues with filters"}]
3. get_action_details("GitHub", "create_pr")
   -> full JSON schema with all parameters, types, descriptions
4. execute_action("GitHub", "create_pr", {"repo": "...", "title": "...", "body": "..."})
   -> result
```

A single handler can serve stages 1-3 by a `stage` argument (`categories`, `actions`, `schema`), returning `{stage, options}` or `{stage, schema}`.

Token budget per stage: stage 1 about 100 tokens (category list); stage 2 about 300-500 (action names and summaries); stage 3 about 500-2000 (full schema of one action); stage 4 variable (execution result). Initial context stays at about 2% of the context window regardless of how many integrations you support.

Best for multi-tenant SaaS where each tenant enables different integrations: the agent discovers what is available for THIS user, not all possible tools.
