# Designing a new MCP server

> Read when: you are about to write tool code for a new MCP server and must decide how to consolidate endpoints, shape schemas, and write descriptions.

<!-- src: audit-agentic-mcp/references/decision-trees/design-phase.md#Designing a New MCP Server | audit-agentic-mcp/references/decision-trees/design-phase.md#Decision Tree -->
## Decision tree

The most impactful decisions come before any tool code: API consolidation, intent-based design, schema shape, description strategy.

```
START: How many API endpoints does this server wrap?
|
+-- 1-3 endpoints
|   +-- Map each to one tool (1:1 is fine at small scale)
|   +-- Keep schemas flat, at most about 6 required params --> mcp/schemas-*
|
+-- 4-10 endpoints
|   +-- Do 3+ endpoints always get called together for one user task?
|   |   +-- YES --> Consolidate into a single intent-based tool
|   |   |         (e.g., deploy_project wraps create + config + deploy + domain)
|   |   |         --> mcp/design-*
|   |   +-- NO  --> Keep separate, but design around user intents
|   |             (verb + resource, not endpoint names)
|   |             --> mcp/design-*
|   +-- Are there CRUD operations across multiple entity types?
|       +-- >3 entity types --> Use combined manage_entity(action=enum) pattern
|       +-- <=3 entity types --> Keep separate CRUD tools
|       --> mcp/design-*
|
+-- 10+ endpoints
|   +-- Group by user intent, not by API path
|   +-- Target <20 tools after consolidation
|   +-- See decisions/tool-count.md for progressive discovery if still >20
|
+-- For ALL tools, apply these design checks:
    +-- Schema shape: Flat, at most about 6 required params, no nesting beyond one level --> mcp/schemas-*
    +-- Description: First 5 words = verb + resource --> mcp/descriptions-*
    +-- Description length: aim at most ~100 tokens, never above 200 --> mcp/descriptions-*
    +-- Parameter names: Unambiguous, self-documenting --> mcp/schemas-*
```

> Note: a description targets at most about 100 tokens, never above 200, the first five words Verb + Resource, and long examples go in the parameter descriptions of the input schema.

<!-- src: audit-agentic-mcp/references/decision-trees/design-phase.md#Key Decision Factors -->
## Key decision factors

| Factor | Options | Recommendation |
|---|---|---|
| API-to-tool mapping | 1:1 mapping vs intent consolidation | Consolidate when 3+ calls always happen together |
| CRUD pattern | Separate tools vs combined action enum | Combine when >3 entity types to keep tool count low |
| Schema depth | Nested objects vs flat params | Always flat; split tool before nesting 2+ levels |
| Parameter count | Few vs many | Target 3-6; split tool if exceeding 15 |
| Description style | Verbose explanation vs front-loaded verb | Front-load verb+resource in first 5 words |

<!-- src: audit-agentic-mcp/references/decision-trees/design-phase.md#When to Re-evaluate -->
## When to re-evaluate

- When you add a 4th entity type to separate CRUD tools (switch to combined pattern).
- When agent transcripts show multi-step call sequences that could be one tool.
- When total tool count crosses 15 (revisit consolidation opportunities).
- When model accuracy drops on tool selection (descriptions may need tightening).
