---
as_of: 2026-04
verify_before_citing: true
---
# Token and cost benchmarks quoted for MCP context design

> Read when: you need the measured numbers behind the MCP context-budget rules (tool-definition share, discovery strategies, code execution, response format, ANSI stripping); verify before citing.

> `as_of` is inferred from the source corpus's April 2026 refresh: the figures below carry no date of their own, so re-check them before citing.

The source gives no dates for these measurements. Core files linking here: `../mcp/budget-tool-definitions.md`, `../mcp/budget-response-size.md`, `../mcp/patterns-progressive-discovery.md`, `../mcp/responses-curated-and-semantic.md`.

## Tool definitions as a share of input tokens

- Community measurement: MCP tool definitions are roughly 15% of Claude Code's total input tokens in a typical session.
- One complex tool server (Playwright MCP) can push that share to 50%.

## Static versus progressive discovery (measured with Claude Sonnet 4)

| Strategy | 40 tools | 100 tools | 200 tools | 400 tools |
|----------|----------|-----------|-----------|-----------|
| Static (all schemas in prompt) | 43,300 tokens | 128,900 | 261,700 | 405,100 |
| Progressive (meta-tools) | 1,600 tokens | 2,400 | 2,500 | 2,500 |

Beyond roughly 200 tools the static approach exceeds Claude's context window and tasks cannot complete at all. Semantic search is reported at about 1.3k initial tokens plus about 3k per task; progressive meta-tools at about 2.5k initial plus about 2.5k per task.

## Code execution with MCP (vendor engineering blog)

- A session with 1,000 tool definitions and a 2-hour transcript drops from 150k tokens to 2k (98.7% reduction).
- A 10,000-row spreadsheet filter task falls from 10k to 0.5k tokens (95%).
- Loop-based Slack polling compresses to a single script call (80%).

## Concise versus detailed responses

Concise responses use about 72 tokens against about 206 for detailed ones: a 65% reduction per call, compounding over workflows of 10+ calls. The headline claim is a 60-70% cut in token usage.

## Stripping terminal decoration (Pare MCP project)

| Command | Before | After | Reduction |
|---|---|---|---|
| `docker build` (multi-stage) | 373 tokens | 20 | 95% |
| `git log --stat` (5 commits) | 4,992 tokens | 382 | 92% |
| `npm install` (487 packages) | 241 tokens | 41 | 83% |
| `vitest run` (28 tests) | 196 tokens | 39 | 80% |
| `cargo build` (2 errors) | 436 tokens | 138 | 68% |

ANSI decoration can inflate CLI output by 5-95x in token terms.

## Serialization formats

YAML is about 30% fewer tokens than the same JSON (47-token example); TSV saves 30-40% (about 40% in the example) versus a JSON array of objects.
