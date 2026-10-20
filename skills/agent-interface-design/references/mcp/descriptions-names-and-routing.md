# Tool names, parameters, strict schemas and routing between tools

> Read when: you are naming tools and parameters, constraining inputs with enums, or telling overlapping tools apart.

Companion to `descriptions-structure-and-length.md` (structure and length budget) and `descriptions-schema-split-and-examples.md` (schema versus description, server instructions, examples). Code: `../frameworks/mcp-python/tool-descriptions.md`.

<!-- src: audit-agentic-mcp/references/patterns/tool-descriptions.md#Pattern 3: Namespace Tools to Prevent Collisions Across MCP Servers -->
## Namespace tool names

With several MCP servers connected to one agent, name collisions cause silent failures or unpredictable routing. Prefix every tool consistently:

```
asana_search_tasks
asana_create_task
jira_search_issues
jira_create_issue
```

Schemes: `{service}_{action}` (`github_create_pr`) or `{service}_{resource}_{action}` (`asana_projects_search`). Pick one and use it everywhere; different LLMs respond better to different schemes, so test with your target model.

Anti-pattern: generic names such as `search`, `create`, `update`, which collide the moment a second server connects. The tool name is the agent's first disambiguation signal; without a namespace the model must rely on description text to tell `search` (contacts) from `search` (files), which fails under context pressure. Allowed characters: `schemas-coercion-and-portability.md`.

<!-- src: audit-agentic-mcp/references/patterns/tool-descriptions.md#Pattern 4: Use Unambiguous Parameter Names -->
## Use unambiguous parameter names

Generic names (`user`, `id`, `data`, `type`) force the model to infer meaning. Specific names are self-documenting and reduce hallucination:

```json
{
  "user_email": "string - the email address of the user to look up",
  "project_id": "string - UUID of the project (use list_projects to find this)",
  "event_type": "string - one of: 'meeting', 'reminder', 'deadline'"
}
```

Additional tips:
- Use enums with `minimum`/`maximum` constraints to tighten validation.
- Mark fields `required` so the model does not guess defaults.
- Add a description to each parameter, not only the tool.
- Reference other tools in parameter descriptions when values come from them ("use list_projects to get this ID").

Rich schemas with enums and descriptions act as inline documentation and cut round-trips and retries by about 25%.

<!-- src: audit-agentic-mcp/references/patterns/tool-descriptions.md#Pattern 5: Enforce Strict Input Schemas with Enums and Constraints -->
## Enforce strict input schemas

Do not rely on description text to communicate valid values; use JSON Schema constraints so they are enforced at the protocol level. A search tool declares `sort` as an enum (`ascending`, `descending`, default descending), `date_range` as an enum (`last_7_days`, `last_30_days`, `last_90_days`, `all_time`, default `last_30_days`) and `limit` as an integer constrained to 1-100 (default 25).

What this gives you:
- Models see the enum values in the schema and pick from them.
- Invalid values are caught before execution with clear validation errors.
- Defaults reduce the number of parameters the model must decide.
- Type hints can generate the JSON Schema automatically in frameworks such as FastMCP.

Anti-pattern: accepting a plain string for everything and hoping the model sends valid values; that yields silent failures or vague errors deep in business logic. Enum size limits: `schemas-flat-and-sized.md`.

<!-- src: audit-agentic-mcp/references/patterns/tool-descriptions.md#Pattern 7: Include Exclusionary Guidance — Tell the Model When NOT to Use a Tool -->
## Say when NOT to use the tool

Positive descriptions are necessary but not sufficient. With overlapping tools the model needs negative routing; without it models default to the "biggest" tool that could technically handle every case.

```json
{"name": "get_customer",
 "description": "Fetch a single customer by ID. Returns full profile with contact info and billing history. Do NOT use for searching — use search_customers instead."}
{"name": "search_customers",
 "description": "Search customers by name or email. Returns top 20 matches. Do NOT use for bulk export; use export_customers for datasets over 100 records."}
{"name": "export_customers",
 "description": "Export all customers matching a filter as CSV. Async — returns a job ID. Do NOT use for single lookups; use get_customer instead."}
```

Real-world example: a design-tool MCP server puts "Do NOT use unless explicitly requested by the user" on its `depth` parameter to stop agents making expensive deep-tree calls by default. Exclusionary guidance acts as a routing table; without it, ambiguity means the model guesses, often wrong.
