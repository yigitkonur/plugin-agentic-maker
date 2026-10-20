# Design MCP tools around user intent

> Read when: you are deciding what tools an MCP server should expose, or auditing a server that wraps one API endpoint per tool.

<!-- src: audit-agentic-mcp/references/patterns/tool-design.md#Tool Design Patterns -->
Structure tools so they map to what the user wants done, minimize round-trips, and work across model sizes. This file covers the single-tool patterns; planners, sandboxes, CRUD and facades are in `design-workflow-planner-and-facade.md`. Code: `../frameworks/mcp-python/tool-design.md`.

<!-- src: audit-agentic-mcp/references/patterns/tool-design.md#Pattern 1: Design Around User Intent, Not API Endpoints -->
## Design around user intent, not API endpoints

Wrapping each API endpoint as its own tool is the most common MCP anti-pattern. It forces the model to orchestrate multi-step workflows that a human developer would automate.

API-centric (bad):

```
get_members()          -> list of member IDs
get_member_activity()  -> activity for one member
get_member_posts()     -> posts for one member
get_member_comments()  -> comments for one member
```

The model calls `get_members`, then loops over the results calling 3 tools per member: tokens burn, errors multiply, 20+ tool calls.

Intent-centric (good): one `get_space_activity(space_id, days=30, sort_by="total_activity")` whose description says what comes back ("members sorted by engagement with their posts, comments, and last active date"). The server does the orchestration and returns `members`, a `summary` string ("Found N members active in the last D days.") and `next_steps` ("Use bulk_message(member_ids=[...]) to contact specific members."). One call instead of 20+, because the server knows the API better than the model ever will.

The "Sable Principle": think about what actions the user would want to take, not what endpoints exist. If the workflow is Get Trending Tracks plus 4 supporting calls, the 4 supporting calls should not be separate tools.

When to consolidate: if 3+ API calls always happen together for a common use case, they belong in one tool.

<!-- src: audit-agentic-mcp/references/patterns/tool-design.md#Pattern 2: Be a Smart Database, Not a Smart Analyst -->
## Be a smart database, not a smart analyst

Provide rich, structured data and let the LLM analyze it. Do not be clever server-side with keyword matching or opaque scoring.

Wrong ("smart analyst"): `analyze_threats(description)` that checks `"payment" in description`, appends "Payment fraud", and caps the list at 5 "for readability". Brittle matching plus an artificial limit.

Right ("smart database"): `get_threat_framework(app_description)` returns the complete framework (for example `stride_categories` with, per category, `description`, `traditional_threats`, `ai_ml_threats`, `mitigation_patterns`, `indicators`), a `context_analysis`, and a `report_template` telling the model to use the framework data to write the report.

Key principles:
1. **Information provider, not analyzer.** Supply the framework, let the LLM apply it.
2. **Completeness over convenience.** Return ALL data with metadata, not truncated slices.
3. **Supply scaffolds, not conclusions.** Provide scoring criteria, not final scores.
4. **Templates, not reports.** Return `report_template` plus raw data, not a finished document.

Bounded exception: if the workflow is read-only and the same follow-up reasoning loop repeats every time, a small server-side planner turn can be justified (a research server that inspects the current result page and returns `recommended_next_queries` or a prefetched next wave). Keep it explicit, bounded and observable; never hide destructive actions or opaque scoring behind the server. Rules: `patterns-bounded-continuation.md`.

The LLM is better at semantic analysis than your keyword matcher; your server is better at retrieval and structured output than the LLM. Play to each side's strengths.

<!-- src: audit-agentic-mcp/references/patterns/tool-design.md#Pattern 3: Consolidate Multi-Step Workflows Into Single Atomic Tools -->
## Consolidate multi-step workflows into one atomic tool

When a common task needs 4+ API endpoints in sequence, wrap the workflow in one tool; the agent does not need the internal steps. Before: `create_project`, `add_env_vars`, `create_deployment`, `add_domain` (4 tools). After: `deploy_project(repo_url, domain, env_vars, branch="main")`, described as "Deploy a new project end-to-end. Creates the project, configures environment variables, deploys from the specified branch, and sets up the custom domain." It returns `status`, `project_id`, `deployment_url`, `domain` and a conversational `message`.

Benefits:
- **Token savings:** one tool description vs four (3-4x reduction).
- **Fewer failure points:** the server handles the sequencing.
- **Friendlier responses:** a conversational summary, not raw status codes.
- **Simpler agent reasoning:** one decision instead of four.

When NOT to consolidate:
- The steps are genuinely independent (the user might want env vars without deployment).
- Individual steps need human confirmation between them.
- The workflow varies significantly between use cases.

Implementation tip: wrap each sub-step so a failure returns a structured error saying which stage failed and what was already completed (see `errors-framing-and-recovery.md`).

<!-- src: audit-agentic-mcp/references/patterns/tool-design.md#Pattern 6: Design Tool Workflows for 3-5 Calls, Not 20+ -->
## Design workflows for 3-5 calls, not 20+

Frontier models handle 20+ sequential tool calls; smaller and open-source models degrade after 5-7 (they forget earlier results, hallucinate parameters, or loop). A server that needs 15 calls for a common task locks you into expensive frontier models.

Design so the most common user goals finish in 3-5 calls. This does not mean fewer tools; it means each tool does more meaningful work per invocation.

Before, 12+ calls to analyze a repo: `list_repos()` (1), `get_repo(id)` (2), `list_branches(repo_id)` (3), `get_branch(repo_id, "main")` (4), `list_commits(branch_id)` (5-6, pagination), `get_commit(commit_id)` (7-12, per commit).

After, 2 calls: `get_repo_activity(repo, days=7, max_commits=20)`, described as "Get recent activity summary for a repository. Returns latest commits, active branches, and contributor stats for the specified time range." It returns `repo`, `default_branch`, `active_branches`, `recent_commits` (`sha[:8]`, `message`, `author`) and a `summary` ("N commits across M branches in the last D days.").

A 3-5 call design works with small models as well as large ones, and cuts latency and token cost by 4-10x.

Tool-count cues for this decision: `../decisions/tool-count.md`. Model-specific degradation reports: `../fresh/mcp-model-behavior.md`.
