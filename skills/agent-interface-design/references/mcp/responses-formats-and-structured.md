# Tool responses: formats, annotations, structuredContent

> Read when: you are choosing a serialization (YAML, TSV, JSON) for tool output, layering content for user versus model, or declaring an outputSchema.

Companion to `responses-curated-and-semantic.md`. Cross-surface format choice: `../decisions/response-format.md`. Code: `../frameworks/mcp-ts/tool-responses.md`, `../frameworks/mcp-ts/tool-responses-structured.md`.

<!-- src: audit-agentic-mcp/references/patterns/tool-responses.md#Pattern 6: Default to YAML Over JSON for LLM-Consumable Responses -->
## Default to YAML over JSON for model-read responses

JSON is the developer default, but YAML is more readable for LLMs and more token-efficient: no curly braces, no quoted keys, no commas. A small component description is 47 tokens as JSON and about 30% fewer as YAML; the model processes both equally well.

Offer a format parameter (for example `output_format` enum `yaml`, `json`, default `yaml`) so the agent can request JSON when it needs programmatic processing. Stick with JSON when the response will be piped into another tool that expects JSON or the agent explicitly asks for it. Let the agent decide; just make YAML the default. One design-tool server defaults to YAML for all design data.

<!-- src: audit-agentic-mcp/references/patterns/tool-responses.md#Pattern 7: Use TSV for Tabular Data to Save 30-40% of Tokens -->
## Use TSV for tabular data (saves 30-40% of tokens)

For table-shaped results (query rows, list outputs, CSV-like records), TSV instead of a JSON array saves 30-40% of tokens (about 40% in the example below), and LLMs parse it correctly with no extra prompting.

JSON repeats every key on every row; for 100 rows x 5 columns that is 500 redundant key strings. TSV states headers once:

```
name	age	city	role
Alice	30	New York	admin
Bob	25	San Francisco	editor
Carol	35	Chicago	viewer
```

Implementation: take the header from the first row's keys, join each row with tabs, return "(no results)" for an empty set, and prefix a one-line count ("Found N users:").

When TSV breaks down: nested objects, arrays within cells, or values containing tabs/newlines. Fall back to YAML or JSON. For the vast majority of database results and list outputs, TSV is the right default.

<!-- src: audit-agentic-mcp/references/patterns/tool-responses.md#Pattern 8: Use Content Annotations to Separate User-Facing and Assistant-Facing Data -->
## Use content annotations to layer user-facing and model-facing data

MCP content blocks accept `annotations` with `audience` and `priority`. Use them to carry debug info, telemetry and internal context that the model can reason about without cluttering the user's view.

Without annotations everything reaches the user: "Found 15 matching records. Cache hit ratio: 0.95, latency: 150ms, query plan: seq_scan on users_idx. 3 results filtered by permission check. Auth token expires in 240s."

With annotations, return two text blocks: the clean summary ("Found 15 matching records.") with `priority: 1.0` and `audience: ["user", "assistant"]`, and a debug block (cache hit, latency, query plan, filtered count, token TTL) with `priority: 0.3` and `audience: ["assistant"]`. The model sees everything and can use the debug data to tune later calls; the user sees the clean summary.

Priority levels:
- `1.0`: critical info the user asked for.
- `0.7`: supplementary context (pagination hints, next steps).
- `0.3`: debug/telemetry for the model only.
- `0.1`: verbose trace data, relevant only if something fails.

Note: client support for annotations varies (`../fresh/mcp-client-and-sdk-quirks.md`). Well-behaved clients respect `audience` and hide assistant-only content; clients that ignore annotations show everything, so keep assistant-only content informative but not confusing if a user sees it.
<!-- src: audit-agentic-mcp/references/patterns/tool-responses.md#Pattern 9: Declare Output Schemas and Return structuredContent -->
## Declare an output schema and return structuredContent

MCP supports output schemas: declare the response shape and the SDK validates it at runtime, giving the model a contract and catching server bugs before they reach the agent.

The critical rule: if you declare an `outputSchema`, you **must** return `structuredContent`. Always return both `structuredContent` and a text `content` block for backward compatibility. Example `get_weather(city)`: output schema `temperature` (number, Celsius), `conditions` (string), `humidity` (number, percent); response:

```json
{
  "content": [{"type": "text", "text": "Oslo: 4C, light rain, 81% humidity"}],
  "structuredContent": {"temperature": 4, "conditions": "light rain", "humidity": 81}
}
```

Why it matters:
1. **Agent reliability:** the model knows the exact shape before calling, so it can plan multi-step workflows without exploratory calls.
2. **Runtime validation:** the SDK rejects malformed responses at the server, not at the agent.
3. **Backward compatibility:** older clients that ignore `structuredContent` still get the text `content`.

Common mistake: declaring an output schema in development, then forgetting to populate `structuredContent`; the TypeScript SDK throws a validation error at runtime (`../fresh/mcp-client-and-sdk-quirks.md`). If you are not ready to commit to a schema, do not declare one; add it when the response shape stabilizes. Code: `../frameworks/mcp-ts/tool-responses-structured.md`.
