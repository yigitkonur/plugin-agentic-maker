# Planner tools, sandboxes, CRUD and facades

> Read when: your MCP server has an ordered pipeline, batch work, many entity types, or 20+ related operations and you need to choose how to expose them.

Companion to `design-intent-based-tools.md`. Code: `../frameworks/mcp-python/tool-design-workflows.md`.

> Reconciled: the sources quote tool-count ceilings of 15, 20, 30 and 50+. This file treats them as diagnostic cues, not verdicts: up to 20 active tools is comfortable (register them eagerly); past about 20, expose only the tools the task needs (groups or session unlocking); about 30 is a warning; 40 or more needs meta-tools (list, describe, execute) (`patterns-progressive-discovery.md`). Per-model figures live in `../fresh/mcp-model-behavior.md`.

<!-- src: audit-agentic-mcp/references/patterns/tool-design.md#Pattern 4: Use a Planner Tool to Teach the Model Your Workflow -->
## Use a planner tool to teach the workflow

For a server whose tools must be called in a specific order, add an explicit planner tool that returns the workflow as structured guidance. Its description says "Get the recommended workflow plan for the current task. Call this FIRST before using any other visualization tools."

The plan response carries a `workflow` array of steps (`step`, `tool`, `description`, optional `required_params`), for example `load_data(file_path)` -> `analyze_columns` -> `create_chart(chart_type, x_column, y_column)` -> `export_dashboard`, plus `instructions` ("Follow these steps in order. Each tool's response will provide specific guidance for the next step.") and `important` ("Do not skip steps. Step 2 output is required for step 3.").

Why it works: the model sees the planner first and has a roadmap; every later tool response reinforces the workflow with next-step hints. A data-visualization server built this way describes the effect as "flattening the agent back into the model".

Key detail: put "Call this FIRST" (or similar) in the planner's description; the model treats it as a strong signal.

Use when: the server has 5+ tools forming a pipeline, order matters, and new users or models cannot intuit the sequence. Steering text in responses is governed by `../decisions/steering-contract.md`.

<!-- src: audit-agentic-mcp/references/patterns/tool-design.md#Pattern 5: Expose a Code Execution Sandbox for Batch Operations -->
## Expose a code-execution sandbox for batch work

For data-heavy tasks (batch processing, pagination, custom analytics), expose one `execute_code` tool that runs LLM-generated code in a sandbox. It is far more token-efficient than dozens of individual tool calls. Input schema: `code` (string, required) and `timeout` (integer, default 300 seconds). The description names the pre-authenticated clients available (for example `salesforce_client`, `s3_client`) and says "Use for batch operations, data processing, or any task requiring loops/parallelism."

Typical generated code: fetch page 1, compute `total_pages = (total_count + 999) // 1000`, fetch the rest with up to 10 parallel workers, upload the combined JSON to storage, and return `{"status", "total", "s3_url"}`. Example in `../frameworks/mcp-python/tool-design-workflows.md`.

Security requirements (non-negotiable):
- Run in isolated containers with `--no-new-privileges`.
- Drop all capabilities, mount a read-only filesystem.
- Enforce CPU/memory limits via cgroups.
- Restrict network egress to whitelisted endpoints.
- Provide API clients pre-authenticated; never expose raw keys.
- Disallow `eval`/`exec` on untrusted strings.
- Set hard timeout limits.

Use when: batch exports, heavy pagination, custom analytics, file transformations, anywhere the final output is a file or URL rather than a conversational response. Token-saving variant: `budget-tool-definitions.md`.

<!-- src: audit-agentic-mcp/references/patterns/tool-design.md#Pattern 7: CRUD — Combined Tool vs Separate Tools Decision -->
## CRUD: combined tool or separate tools

The answer depends on tool count and approval requirements.

Combine when you have many entity types (users, projects, teams, billing). Four CRUD operations x 8 entities = 32 tools; combining gives 8. Keep separate when you have 3 or fewer entity types, need per-operation approval (reads auto-approved, deletes confirmed), or the operations have very different parameter shapes.

Combined shape: `manage_user(action, user_id=None, filters=None, data=None)` with `action` an enum of `list`, `get`, `create`, `update`, `delete`, and a description that spells out each action ("'list' (filter by role/status), 'get' (by user_id), 'create' (name+email required), 'update' (user_id + fields to change), 'delete' (by user_id, irreversible)"). Each action returns its own result and a `status` (`created`, `updated`, `deleted`).

| Factor | Combine | Separate |
|---|---|---|
| Entity types | >3 | 3 or fewer |
| Total tool count | Approaching 20+ | Under 15 |
| Approval granularity | Same for all ops | Different per operation |
| Parameter overlap | High | Low |

Tool count affects model accuracy: with 30+ tools, models frequently pick the wrong tool or hallucinate parameters. Decision tree: `../decisions/tool-count.md`.

<!-- src: audit-agentic-mcp/references/patterns/tool-design.md#Pattern 8: The Toolhost/Facade Pattern for Many Related Operations -->
## Toolhost / facade for many related operations

With 20+ closely related operations, use one dispatcher tool that routes to internal handlers via an `operation` parameter (the Gang of Four Facade applied to MCP). The model picks the operation from a documented list; shared logic (auth, logging, error handling) lives in the facade.

Shape: a registry maps each operation (`list_users`, `get_user`, `create_user`, `list_projects`, `get_project`, `export_data`) to a handler and its argument names. The tool `admin_toolhost(operation, args={})` has a description that lists every operation name ("Admin API gateway. Operations: ... Pass the operation name and its arguments."). It returns an error naming the available operations for an unknown one, an error naming the missing args, and otherwise `{"operation", "status": "success", "result"}`; handler exceptions come back as `status: "error"` with the message.

Use when:
- 20+ operations share common auth/validation/error-handling code.
- Operations are closely related (same domain, same API backend).
- You want one place for logging, rate limiting or retry logic.

Avoid when:
- Fewer than 5 operations: the indirection adds complexity for no benefit.
- Operations need individual user-approval flows (the facade hides which operation runs).
- Operations have radically different parameter shapes that do not fit a generic `args` dict.

The pattern scales to 50+ operations without model confusion. The trade-off is discoverability: the model must know which operations exist, so the description string must be comprehensive. Action-routed variant for a single resource: `schemas-flat-and-sized.md`.
