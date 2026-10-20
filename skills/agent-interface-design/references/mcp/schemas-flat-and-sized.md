# Input schema shape: flat, small, enumerated

> Read when: you are designing or reviewing the parameters of an MCP tool: how many, how nested, which formats, how enums are described.

How to keep tool input schemas simple enough for LLMs to fill correctly. Coercion, regex errors, safe names and cross-model rules are in `schemas-coercion-and-portability.md`. Code (TypeScript): `../frameworks/mcp-ts/schema-design-shapes.md`.

<!-- src: audit-agentic-mcp/references/patterns/schema-design.md#Schema Design Patterns -->
Schema complexity directly drives tool-call accuracy. The rules below cover complexity limits, flexible formats, enum descriptions and splitting oversized tools.

> Note: avoid `oneOf`/`anyOf` at the top of an input schema; inline enums up to 10 values; above 10, describe the values and validate on the server. The 20-value report is model-specific: `../fresh/mcp-model-behavior.md`.

<!-- src: audit-agentic-mcp/references/patterns/schema-design.md#Pattern 3: Keep Schemas Flat, Under 6 Parameters | audit-agentic-mcp/references/patterns/schema-design.md#Rules of Thumb -->
## Keep schemas flat, under 6 parameters

Community experience consistently shows flat schemas with 3-6 parameters reach significantly higher parse success than nested ones. GPT models are especially prone to "self-checking" on nested schemas: they build a valid input, second-guess it, and refuse to call the tool.

Bad (nested): `search(query, filters: {dateRange: {start, end}, status: enum[active, archived], tags: [string]})`.

Good (flat, same capability): `search(query, startDate? "Start date (ISO 8601)", endDate? "End date (ISO 8601)", status? enum[active, archived], tags? "Comma-separated tags")`.

Rules of thumb:
1. **3-6 params** is the sweet spot: high accuracy, enough expressiveness.
2. **Never nest 2+ levels**; accuracy drops significantly.
3. If you need complexity, **split into multiple tools** rather than one complex schema.
4. An array of primitives is acceptable; an array of objects is risky.

<!-- src: audit-agentic-mcp/references/patterns/schema-design.md#Pattern 4: Accept Flexible Formats, Normalize Server-Side | audit-agentic-mcp/references/patterns/schema-design.md#Applies Beyond Dates -->
## Accept flexible formats, normalize server-side

LLMs express one concept in many formats. Do not force one in the schema; accept a loose string and parse it yourself. Flexible string inputs reach higher accuracy than union types (`anyOf`, `z.union()`), which LLMs often mishandle by picking the wrong branch or producing a malformed hybrid.

Bad: `date` as a union of an ISO datetime string, a number ("Unix timestamp"), and an enum (`today`, `yesterday`, `last_week`).

Good: `date` as one string described "Date in any format: ISO 8601, Unix timestamp, or relative ('yesterday', 'last week')". Parse in the handler with a date parser, falling back to the platform date constructor; if parsing fails, return a teaching message such as "Could not parse date. Try ISO 8601 like '2024-01-15'." (see `errors-protocol-vs-tool.md`). Echo what you understood: `errors-framing-and-recovery.md`.

Applies beyond dates: file paths and identifiers. Accept loose formats and resolve them server-side.

<!-- src: audit-agentic-mcp/references/patterns/schema-design.md#Pattern 5: Describe Each Enum Value Inline | audit-agentic-mcp/references/patterns/schema-design.md#More Examples -->
## Describe each enum value inline

Do not just list enum values; explain what each means in the parameter description, so the model gets semantics, not labels. Enums beat free-form strings for valid-call rate, and inline value descriptions push accuracy higher and reduce wrong-value picks.

Bad: `livecrawl` enum `fallback`, `preferred` with no context.

Good: same enum described "Live crawl mode - 'fallback': use live crawling as backup if cached version is unavailable, 'preferred': always prioritize live crawling over cache (default: 'fallback')". A search-API server did exactly this: without the description LLMs defaulted to `preferred` (it sounds better), wasting crawl budget; with it they correctly default to `fallback`.

More examples:
- `level`: "'error': only critical failures, 'warn': errors + potential issues, 'info': general operational events, 'debug': verbose output for troubleshooting".
- `format` (`json`, `csv`, `markdown`): "'json': structured data for programmatic use, 'csv': tabular data for spreadsheets, 'markdown': human-readable formatted output".

Enum size: up to 10 values inline; above 10, describe values and validate server-side (see the note above).

<!-- src: audit-agentic-mcp/references/patterns/schema-design.md#Pattern 6: Break Tools Over 40 Parameters | audit-agentic-mcp/references/patterns/schema-design.md#Strategy 1: Split by Workflow Stage | audit-agentic-mcp/references/patterns/schema-design.md#Strategy 2: Action-Routed Facade | audit-agentic-mcp/references/patterns/schema-design.md#Rules -->
## Split tools with too many parameters

LLMs struggle increasingly as parameter count rises. Keep tools under 6 parameters for best results and split any tool exceeding 15-20.

Strategy 1, split by workflow stage: one `deploy` tool with 30+ params (`env`, `region`, `scaling`, `healthCheck`, `rollback`, ...) becomes three: `deploy_configure(env enum[staging, production], region)`, `deploy_execute(configId "ID from deploy_configure", strategy enum[rolling, blue-green])`, `deploy_verify(deploymentId "ID from deploy_execute")`.

Strategy 2, action-routed facade: `database(action enum[query, insert, schema], table, where? "Only for 'query'", data? "Only for 'insert'")`. For many resources see the toolhost pattern in `design-workflow-planner-and-facade.md`.

Rules by parameter count:
1. **Under 6:** ideal.
2. **6-15:** acceptable if flat.
3. **15-40:** split into 2-3 tools.
4. **40+:** mandatory split.
