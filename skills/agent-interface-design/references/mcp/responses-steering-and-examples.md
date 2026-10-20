# Tool responses: next-step hints, example responses, search frontier

> Read when: you want a tool response to tell the agent what to do next, to document its own return shape, or to return a research frontier instead of one result page.

Rules for steering text in tool output (authority, namespacing, `allowed_next_tools`) live in `../decisions/steering-contract.md`; read it before adding any hint beyond a plain tool name. Code: `../frameworks/mcp-python/tool-responses.md`, `../frameworks/mcp-ts/tool-responses-structured.md`.

<!-- src: audit-agentic-mcp/references/patterns/tool-responses.md#Pattern 5: Include Next-Step Hints in Successful Responses -->
## Include next-step hints in successful responses

Do not just return data; tell the model what it can do next ("HATEOAS at the language level"). Example: `create_project(name, repo_url)` returns `status`, `project_id`, `project_name`, a `message`, and `next_steps`:
- "Use add_environment_variables(project_id='...') to configure env vars."
- "Use create_deployment(project_id='...', branch='main') to deploy."
- "Use add_custom_domain(project_id='...', domain='...') to set up a domain."

Why it works: the model has no memory of your API's workflow. A developer reads the docs and knows that after creating a project you configure env vars and deploy; the model does not know unless the response says so.

Guidelines:
- Keep hints specific: name the exact tool and include required parameter values.
- Order hints by likelihood (most common next action first).
- Include only 2-4 hints to avoid overwhelming the context.
- Use the actual parameter values from the current response; do not make the model guess.

Real-world example: a data-visualization server's planner tool returns structured guidance about call order, and every later response reinforces it. See the planner pattern in `design-workflow-planner-and-facade.md`.

<!-- src: audit-agentic-mcp/references/patterns/tool-responses.md#Pattern 10: Put Example Responses in Tool Descriptions -->
## Put example responses in tool descriptions

Include a concrete example response in the tool's description. The agent learns the shape and plans follow-up calls without a throwaway exploratory call: one example in the description saves one round-trip at runtime.

Without an example (`list_users`: "List users in the workspace") the agent guesses or wastes a call. With one, the description lists the fields ("users": array of {id, name, email, role}; "total": total count, may exceed returned results; "has_more": whether more pages exist), shows a two-record JSON example with `total: 47` and `has_more: true`, and adds "Use "page" param to paginate. Pass user "id" values to get_user_details."

What this unlocks:
- The agent can destructure the response correctly on the first try.
- It knows `has_more` exists and paginates automatically.
- It knows to pass `id` (not `name` or `email`) to downstream tools.
- It does not make a dummy call just to discover the format.

Keep examples minimal: one or two records, not a full page. The agent extrapolates the pattern. The description gets longer, which purists dislike, but agents that see example responses make fewer errors and fewer exploratory calls.

> Reconciled: that example description exceeds the 100-token target. The length rule (`descriptions-structure-and-length.md`) wins: at most about 100 tokens, never above 200, with long examples in the parameter descriptions or the output schema (`responses-formats-and-structured.md`).

<!-- src: audit-agentic-mcp/references/patterns/tool-responses.md#Pattern 11: Return a Search Frontier, Not Just the First SERP -->
## Return a search frontier, not just the first result page

For research, SEO and discovery tools, the first result page is rarely the finished product. Return the **current frontier** for the next step, not just current evidence.

Weak: `{"results": ["10 search results here"]}`.

Agentic:

```json
{
  "summary": "The current SERP is strong on general overviews but weak on implementation examples and CLI translation.",
  "results": ["10 search results here"],
  "coverage_gaps": [
    "Few concrete MCP implementation examples",
    "Almost no CLI-specific steering guidance",
    "Low source diversity across the top results"
  ],
  "recommended_next_queries": [
    {"query": "seo research mcp implementation example",
     "reason": "Fill the implementation gap",
     "expected_signal": "production patterns"},
    {"query": "agentic cli steering for seo workflows",
     "reason": "Translate MCP steering patterns into CLI output contracts",
     "expected_signal": "CLI design patterns"}
  ],
  "recommended_next_tool": "fetch_pages",
  "server_actions_taken": [
    {"type": "internal_planner_turn",
     "purpose": "derive next-query candidates from the current results"}
  ],
  "stop_conditions": [
    "Stop if two consecutive follow-up waves add no novel authoritative sources."
  ]
}
```

Strong example: a secure research server takes a seed keyword, runs dozens of searches, then uses an internal model turn to decide which keywords to search next from the returned results. The gain is collapsing a repeated "inspect results -> pick next keywords -> search again" loop into one bounded server response.

Good research is **coverage management**: intent coverage, source diversity, freshness, implementation depth, authority mix.

How to steer well:
1. Return the **gap model**, not just the current answer.
2. Recommend next steps as ranked, structured objects, not prose.
3. Separate `server_actions_taken` from `recommended_next_queries` so the agent knows what already happened.
4. Prefer recommendations that remove the biggest information bottleneck first.
5. Bound internal continuation with spend, time and wave caps (`patterns-bounded-continuation.md`).

Do not hide opaque autonomy inside the tool. If you use an internal planner or a second model call, disclose it in the response; that keeps the system debuggable and lets you evaluate whether the steering helps.
