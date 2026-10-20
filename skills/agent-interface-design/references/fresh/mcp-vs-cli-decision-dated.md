---
as_of: 2026-04-15
verify_before_citing: true
---
# MCP vs CLI: Dated Evidence

> Read when: you need the documented facts, the benchmark numbers or the community reports behind the surface-choice rules, with their dates. Verify before citing.

The decision rules are in `../decisions/surface-choice.md`; the same benchmark from the MCP side is in `mcp-vs-cli-benchmarks.md`. Everything below is time-sensitive: the source states "refreshed on April 15, 2026", and vendor behaviour, spec versions and benchmark figures move.

<!-- src: audit-agentic-cli/references/mcp-vs-cli-decision.md#2. What the Official Docs Establish -->
## What the official docs establish

| Documented fact | Why it matters for the decision |
|---|---|
| MCP is a JSON-RPC protocol with `stdio` and Streamable HTTP transports. | MCP is not "just remote tools." It can be local or remote, but it always adds a protocol layer. |
| MCP servers expose typed discovery through `tools/list`, `inputSchema`, resources, and prompts. | Choose MCP when schema-level discovery and machine-readable tool contracts are the point. |
| HTTP-based MCP authorization is specified around OAuth 2.1 style metadata and bearer tokens; `stdio` transports should use environment credentials instead. | MCP is much better matched to governed remote access than to local shell-style credential handling. |
| Anthropic and OpenAI both document approvals, allowlists, deferred loading, and strong warnings about untrusted servers. | MCP earns its cost when approval and trust boundaries matter, not just a way to run commands. |
| Shell and local-shell tools run in the caller's own runtime, with safety coming from sandboxing, allowlists, hooks, and permissions. | CLI-first is usually simpler and cheaper, but the caller owns the blast radius. |

Primary docs named by the source (as of 2026-04-15):

- Model Context Protocol architecture: `https://modelcontextprotocol.io/docs/learn/architecture`
- MCP transports spec, November 25, 2025: `https://modelcontextprotocol.io/specification/2025-11-25/basic/transports`
- MCP authorization spec, June 18, 2025: `https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization`
- Anthropic MCP connector: `https://docs.anthropic.com/en/docs/agents-and-tools/mcp-connector`
- Claude Code MCP: `https://docs.anthropic.com/en/docs/claude-code/mcp`
- OpenAI MCP guide: `https://developers.openai.com/api/docs/mcp`
- OpenAI local shell: `https://developers.openai.com/api/docs/guides/tools-local-shell`
- GitHub Copilot CLI programmatic reference: `https://docs.github.com/en/enterprise-cloud@latest/copilot/reference/copilot-cli-reference/cli-programmatic-reference`

<!-- src: audit-agentic-cli/references/mcp-vs-cli-decision.md#7. Current Evidence And Caveats | audit-agentic-cli/references/mcp-vs-cli-decision.md#7.1 Documented benchmark signal -->
## Benchmark signal

The strongest public benchmark the source found is Scalekit's March 11, 2026 comparison of GitHub tasks using Claude Sonnet 4:

- 75 total benchmark runs;
- same tasks and prompts, with only the tool interface changing;
- CLI medians ranged from 1,365 to 8,750 tokens;
- direct MCP medians ranged from 32,279 to 82,835 tokens;
- the CLI completed 25 of 25 runs in the reported setup;
- the tested direct MCP path completed 18 of 25 runs.

Source: `https://www.scalekit.com/blog/mcp-vs-cli-use` (March 11, 2026).

<!-- src: audit-agentic-cli/references/mcp-vs-cli-decision.md#7.2 What that benchmark does not prove -->
## What the benchmark does not prove

Do not overgeneralize it. The caveats:

- it focused on GitHub tasks;
- it used a large GitHub MCP tool catalog;
- some failures were connection or timeout issues, not protocol impossibilities;
- it shows the cost of a specific MCP surface, not a universal ceiling for all MCP designs.

The correct takeaway is narrower:

- a CLI is the better default when a strong CLI already exists;
- bloated or eagerly loaded MCP surfaces carry real cost;
- gateway filtering and deferred loading materially change the tradeoff.

<!-- src: audit-agentic-cli/references/mcp-vs-cli-decision.md#7.3 Practitioner signal from Reddit -->
## Practitioner signal

Across the Reddit threads the source reviewed on April 15, 2026, the pattern was consistent.

| Theme | Reports |
|---|---|
| Pro-CLI | lower token usage; easier debugging; better results with mature CLIs like `gh`, `kubectl` and `aws`; fewer moving parts for coding agents |
| Pro-MCP | per-user OAuth; governed remote access; non-technical user surfaces; stateful tools and shared connectors |
| CLI complaints | permission prompts; quoting and shell expansion friction; broad local access if safeguards are weak |
| MCP complaints | auth drift; timeouts; schema bloat; low-quality community servers |

Treat this as practitioner evidence, not a controlled study. Threads the source cited:

- r/ClaudeAI, "Switched from MCPs to CLIs": `https://www.reddit.com/r/ClaudeAI/comments/1sakut1/switched_from_mcps_to_clis_for_claude_code_and/`
- r/AI_Agents, "The Truth About MCP vs CLI": `https://www.reddit.com/r/AI_Agents/comments/1rjtp3q/the_truth_about_mcp_vs_cli/`
- r/ClaudeCode, "CLI permission requests vs MCP": `https://www.reddit.com/r/ClaudeCode/comments/1rwz2km/to_everyone_touting_the_benefits_of_cli_tooling/`
- r/mcp, "MCPs, CLIs, and skills": `https://www.reddit.com/r/mcp/comments/1rtsl9z/mcps_clis_and_skills_when_to_use_what/`
