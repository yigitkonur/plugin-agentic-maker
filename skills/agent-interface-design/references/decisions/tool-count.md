# Handling a growing tool count

> Read when: an MCP server exposes, or will expose, more than about 10 tools and you must choose between pruning, grouping, meta-tools, and semantic search.

<!-- src: audit-agentic-mcp/references/decision-trees/tool-count.md#How to Handle Growing Tool Count | audit-agentic-mcp/references/decision-trees/tool-count.md#Decision Tree -->
## Decision tree

Every tool in the prompt costs tokens and degrades routing accuracy past a model-specific threshold. Treat the numbers below as diagnostic cues, not verdicts.

> Reconciled: the sources gave tool-count ceilings of 10, 20, 30 and 40 and different per-model caps; this file uses up to 20 active tools as the default comfortable range, about 30 as a warning, and 40 or more as the point where progressive discovery is needed. Per-model sweet spots and client caps are in `fresh/tool-count-by-model.md`.

```
START: How many tools does your server expose?
|
+-- <10 tools
|   +-- No action needed. Static tool list is fine.
|   +-- Ensure descriptions are concise (aim ~100 tokens each, never above 200)
|   +-- --> mcp/descriptions-*
|
+-- 10-20 tools  (default comfortable range)
|   +-- Which model will consume these tools?
|   |   +-- Check that model's sweet spot --> fresh/tool-count-by-model.md
|   +-- Can you consolidate CRUD into action-enum patterns?
|   |   +-- YES --> Reduce 4 tools per entity to 1 --> mcp/design-*
|   |   +-- NO  --> Organize with clear namespacing (prefix__tool)
|   +-- --> mcp/budget-*
|
+-- 20-40 tools  (about 30 is a warning)
|   +-- Use progressive discovery (expose only relevant tools per task)
|   +-- Option A: Tool groups -- predefine groups, expose per context
|   |   (e.g., "code-review" group = read_file, search_code, get_diff)
|   +-- Option B: Session-based unlocking -- start with 3-5 always-on
|   |   tools, unlock more as the task becomes clear
|   +-- Keep the target model's active-set cap in mind (fresh/tool-count-by-model.md)
|   +-- --> mcp/budget-*
|
+-- 40-100 tools  (progressive discovery needed)
|   +-- Use meta-tools: list_tools / describe_tools / execute_tool
|   +-- Only 3 tools in prompt regardless of catalog size
|   +-- Hierarchical prefixes for tool IDs (/domain/entity/action)
|   +-- Initial context far smaller than a static list (figures: fresh/decision-tree-benchmarks.md)
|   +-- --> mcp/budget-*
|
+-- 100+ tools
    +-- Use semantic search with embeddings
    +-- Single find_tools(query) meta-tool + execute_tool
    +-- Pre-compute embeddings offline; query FAISS/Pinecone at runtime
    +-- Best for simple single-intent queries (small initial context)
    +-- For complex multi-step workflows, prefer 4-stage progressive
    |   disclosure (discover_categories -> get_actions -> get_schema
    |   -> execute)
    +-- --> mcp/budget-*
```

<!-- src: audit-agentic-mcp/references/decision-trees/tool-count.md#Key Decision Factors -->
## Key decision factors

| Factor | Options | Recommendation |
|---|---|---|
| Tool count vs model limit | Static list vs dynamic discovery | Go dynamic when exceeding the model's sweet spot |
| Discovery pattern | Groups / meta-tools / semantic search | Groups <40, meta-tools 40-100, semantic 100+ |
| Token budget | Full schemas vs on-demand | On-demand saves most tokens at 100+ tools (figure: `fresh/decision-tree-benchmarks.md`) |
| Query complexity | Simple intent vs multi-step workflow | Semantic for simple; progressive for multi-step |
| Cache invalidation | Static at startup vs dynamic | Dynamic tool lists nuke prefix cache; use notifications |

<!-- src: audit-agentic-mcp/references/decision-trees/tool-count.md#When to Re-evaluate -->
## When to re-evaluate

- When tool count crosses the next threshold (10, 20, 40, 100).
- When switching target models (each has different sweet spots).
- When agents start calling wrong tools or hallucinating tool names.
- When initial prompt token count exceeds 40k (compress via discovery).
