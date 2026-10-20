# Tool descriptions: structure and length

> Read when: you are writing or trimming an MCP tool description and need its structure, first words and length budget.

<!-- src: audit-agentic-mcp/references/patterns/tool-descriptions.md#Tool Description Patterns -->
Tool descriptions are the model's only guide to when and how to use a tool. These patterns cover structure and length; routing between tools is in `descriptions-names-and-routing.md`; the schema/description split, server instructions and examples are in `descriptions-schema-split-and-examples.md`. Code: `../frameworks/mcp-ts/tool-descriptions.md`, `../frameworks/mcp-python/tool-descriptions.md`.

> Reconciled: the sources gave three length numbers (about 100 tokens in one pattern, 200 in another, a 320-token example called too long). This file uses: target at most about 100 tokens, never above 200; the first five words are Verb + Resource; long examples go in the parameter descriptions of the input schema.

<!-- src: audit-agentic-mcp/references/patterns/tool-descriptions.md#Pattern 1: Use XML Tags to Separate Purpose from Instructions -->
## Separate purpose from instructions with tags

Structuring a description with XML tags improves selection accuracy because the model can separate "what it is for" from "how to use it". LLMs have strong XML parsing priors; a flat paragraph mixing purpose and usage gets muddled.

```xml
<usecase>Retrieves member activity for a space, including posts, comments, and last active date. Useful for tracking activity of users.</usecase>
<instructions>Returns members sorted by total activity. Includes last 30 days by default.</instructions>
```

The model matches intent against `<usecase>` and extracts parameters from `<instructions>`. In testing this reduced selection errors versus free text, especially when several tools overlap. Keep the tagged text inside the length budget below.

<!-- src: audit-agentic-mcp/references/patterns/tool-descriptions.md#Pattern 2: Write Descriptions Like Briefing a New Hire -->
## Brief the model like a new hire

The model has zero institutional knowledge and every conversation starts fresh. Write as if explaining the tool to a competent new hire on day one:
- State the tool's **single, clear purpose** explicitly.
- Define domain-specific terminology.
- Make implicit conventions explicit (for example, "dates are in YYYY-MM-DD format").
- Include a brief usage example showing expected input/output.
- Specify what the tool does NOT do, to prevent misuse.

Example (`search_contacts`): "Search the CRM for contacts matching criteria. Returns contact records with name, email, and company. Use this when the user asks to find, look up, or search for people. Do NOT use this for updating contacts - use update_contact instead. Example: search_contacts(query="Jane at Acme") returns matching contacts. Supports partial name matching and company name filtering."

Small, measured description refinements have produced large accuracy gains (a vendor report on a coding benchmark; description quality was one of several factors, see `../fresh/mcp-model-behavior.md`). Mind the length budget: this example is the upper end.

<!-- src: audit-agentic-mcp/references/patterns/tool-descriptions.md#Pattern 6: Front-Load Verb + Resource in the First Five Words -->
## Front-load Verb + Resource in the first five words

LLMs skim descriptions like headlines; the first words carry disproportionate weight in selection. Filler ("This tool is used to...") wastes the attention budget before the signal arrives.

Structure: **Verb + Resource + key scope**, then stop. Keep the total under about 100 tokens.

```json
{"name": "search_customers",
 "description": "Search customers by name, email, or account ID. Returns top 20 matches with account status. Use list_customers for unfiltered pagination."}
{"name": "create_invoice",
 "description": "Create a draft invoice for a customer. Requires customer_id and at least one line item. Does not send — use send_invoice to deliver."}
```

Anti-pattern: "This tool provides the ability to search through the customer database using various criteria including but not limited to name, email address, and account identifier. It will return a paginated list of results sorted by relevance score with additional metadata about each customer's current account status and tier level." That is 50+ tokens before the model learns what the tool does.

Key principle: first 5 words -> selection. Next 20 words -> parameters. Everything after that -> diminishing returns.

<!-- src: audit-agentic-mcp/references/patterns/tool-descriptions.md#Pattern 11: Over-Verbose Descriptions Reduce Tool Call Rate -->
## Over-verbose descriptions reduce the tool call rate

Descriptions over about 200 tokens make LLMs call the tool less often, even when it is the right one (community evaluations; treat as a reported effect). One hypothesis: a description long enough to read like a mini-essay competes with generation, and the model "answers" from the description text instead of calling the tool.

<!-- src: audit-agentic-mcp/references/patterns/tool-descriptions.md#The 200-Token Rule -->
### The 200-token rule

Measure description tokens before registering; warn above 200 (hard ceiling) and aim for about 100. A 400-token description costs more tokens AND gets called less. Check code: `../frameworks/mcp-ts/tool-descriptions.md`.

<!-- src: audit-agentic-mcp/references/patterns/tool-descriptions.md#Optimal Format: Verb + Object + Key Constraint -->
### Optimal format: Verb + Object + Key Constraint

Too long (320 tokens): "This tool allows you to search through the repository's codebase using semantic or keyword-based queries. It supports both exact string matching and fuzzy semantic search using vector embeddings. The results will include file paths, line numbers, and surrounding context..."

Optimal (about 35 tokens): "Search codebase by keyword or semantic query. Returns file paths, line numbers, and snippets. Use for finding functions, variables, or concepts. Filter by file type or directory with optional params."

<!-- src: audit-agentic-mcp/references/patterns/tool-descriptions.md#What Belongs in Schema, Not Description -->
### What belongs in the schema, not the description

Move parameter-level guidance into each parameter's own `description`. The model reads parameter descriptions exactly when it fills in arguments. Example: `query` described as "Search term. Supports regex if prefixed with 're:'"; `file_type` described as "Filter by extension, e.g. '.ts' or '.py'" (TypeScript form in the framework file). The optimal tool description is short enough to scan and specific enough to select.
