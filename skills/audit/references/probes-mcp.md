# The MCP probes

> Read when: you run, or have to explain, `agentic-maker probe mcp` or `scan mcp`, including what replaced the old budget and static-audit scripts. CLI probes: [probes-cli](probes-cli.md).

<!-- src: audit-agentic-mcp/scripts/measure-context-budget.sh.md#measure-context-budget.sh -->
## `probe mcp` (replaces `measure-context-budget.sh`)

The old script estimated the context cost of an MCP server by grepping source for tool registrations, descriptions, schema blocks and response examples. `probe mcp` connects to the server and measures the real thing: the `tools/list` response a client receives. Budget numbers are `chars / 4` over the JSON of each definition (a labelled heuristic, not a tokenizer), so they match a hand count of the raw response exactly.

<!-- src: audit-agentic-mcp/scripts/measure-context-budget.sh.md#Usage -->
### Usage
```
agentic-maker probe mcp "python3 /abs/path/server.py" --budget
agentic-maker probe mcp http://127.0.0.1:8000/mcp --tool-threshold 15
agentic-maker probe mcp .mcp.json --server docs --description-chars 280
agentic-maker probe mcp "node dist/index.js" --call 'search={"q":"test"}'
```
A stdio server is started in an empty temp directory with a minimal environment (`--cwd` and `--env K=V` override); an `http(s)` URL is spoken to as unauthenticated Streamable HTTP. A server that answers 401/403 is reported as not measured: use `mcpc` or the MCP Inspector CLI for it, or capture its `tools/list` yourself.

<!-- src: audit-agentic-mcp/scripts/measure-context-budget.sh.md#Options -->
### Options
| Flag | Default | Effect |
|---|---:|---|
| `--description-chars N` | 400 | flag a tool description longer than N characters (above 800, about 200 tokens, it is Medium) |
| `--schema-chars N` | 2000 | flag an input schema longer than N characters |
| `--response-chars N` | 4000 | flag a `--call` response longer than N characters (O8) |
| `--tool-threshold N` | 20 | flag more than N tools (N+10 is the warning size, 40 or more needs progressive discovery) |
| `--call NAME=JSON` | none | call this tool; only read-only tools |
| `--budget` | on | kept for compatibility; the budget is always computed |

<!-- src: audit-agentic-mcp/scripts/measure-context-budget.sh.md#What it reports -->
### What it reports
The tool count; per tool its description, schema and total definition size and an estimated token count; the five largest definitions; per-tool findings (missing or over-long description, unsafe name, near-duplicate descriptions, wide or deep or `oneOf` schemas, big enums, a destructive-looking tool with no `destructiveHint`, missing annotations); `--call` response sizes and failures reported as success; stdout pollution on stdio. Each finding names the reference to read.

<!-- src: audit-agentic-mcp/scripts/measure-context-budget.sh.md#Design constraints -->
### Design constraints
It sends only `initialize`, `tools/list` (paged), `prompts/list` and `resources/list` when advertised, and `tools/call` for tools you named. It writes nothing outside a temp directory, refuses server-initiated requests instead of hanging, and has a timeout per request. It needs only the Python standard library.

<!-- src: audit-agentic-mcp/scripts/measure-context-budget.sh.md#Exit codes -->
### Exit codes
0 no findings; 8 findings; 2 bad arguments; 3 command or config not found; 4 the server needs authentication; 6 initialize or tools/list failed; 7 cannot connect or the server timed out.

<!-- src: audit-agentic-mcp/scripts/measure-context-budget.sh.md#When to run -->
### When to run
During context and cost audits; before and after trimming descriptions or splitting a large tool surface; before enabling prompt caching where tool-list stability matters.

<!-- src: audit-agentic-mcp/scripts/audit-mcp-server.sh.md#audit-mcp-server.sh -->
## `scan mcp` (replaces `audit-mcp-server.sh`)

A read-only static triage: where the MCP code is and which risky patterns occur. It locates; it does not decide. Confirm every candidate in the source, and measure the running server with `probe mcp`.

<!-- src: audit-agentic-mcp/scripts/audit-mcp-server.sh.md#Usage -->
### Usage
`agentic-maker scan mcp [path]` (default: the current directory). `agentic-maker detect [path]` lists every kind of surface (skills, plugins, MCP, CLIs) in one pass.

<!-- src: audit-agentic-mcp/scripts/audit-mcp-server.sh.md#What it reports -->
### What it reports
Likely MCP entrypoints and registrations per ecosystem (`registerTool`, `server.tool(`, `@mcp.tool`, `#[tool]`, `AddTool`, `FastMCP(`, `.mcp.json`), framework signals (`mcp-use`, `@modelcontextprotocol/sdk`, `@modelcontextprotocol/server`, Python FastMCP, rmcp, mcp-go), counts and the first matches of tool registrations, schemas, annotations, error handling, deprecated SSE transport signals, and stdout logging patterns that can break stdio transports.

<!-- src: audit-agentic-mcp/scripts/audit-mcp-server.sh.md#Design constraints -->
### Design constraints
Read-only; regex rather than an AST, so counts are candidates and not confirmed tools; common dependency and build directories are skipped. The rules are data (`data/surfaces.tsv`), so another ecosystem is one more row.

<!-- src: audit-agentic-mcp/scripts/audit-mcp-server.sh.md#Exit codes -->
### Exit codes
0 scan completed; 2 bad arguments; 3 the path does not exist.

<!-- src: audit-agentic-mcp/scripts/audit-mcp-server.sh.md#When to run -->
### When to run
At the start of a quick audit of an existing server; before choosing a companion build route (`decisions/companion-routing.md`); after a large refactor, to re-check the obvious static regressions.
