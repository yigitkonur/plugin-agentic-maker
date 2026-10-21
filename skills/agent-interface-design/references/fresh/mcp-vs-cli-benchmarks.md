---
as_of: 2026-04-15
verify_before_citing: true
---

# MCP vs CLI: dated benchmark and community evidence

> Read when: you need numbers or practitioner themes for the MCP-vs-CLI decision, or the primary doc links behind `decisions/mcp-vs-cli-evidence.md`. All items are dated; re-check before citing.

Status: refreshed on April 15, 2026.

<!-- src: audit-agentic-mcp/references/patterns/mcp-vs-cli.md#10. Current Evidence And Caveats -->
## Current evidence and caveats

<!-- src: audit-agentic-mcp/references/patterns/mcp-vs-cli.md#10.1 Benchmark signal -->
### Benchmark signal

The strongest public benchmark found: Scalekit's March 11, 2026 comparison of GitHub tasks using Claude Sonnet 4 (https://www.scalekit.com/blog/mcp-vs-cli-use).

- 75 total benchmark runs; same tasks and prompts, only the tool interface changed.
- CLI medians ranged from 1,365 to 8,750 tokens.
- Direct MCP medians ranged from 32,279 to 82,835 tokens.
- CLI completed 25 of 25 runs in the reported setup.
- The tested direct MCP path completed 18 of 25 runs.

<!-- src: audit-agentic-mcp/references/patterns/mcp-vs-cli.md#10.2 What that benchmark means -->
### What that benchmark means

It does not prove that "MCP is bad." It does show:

- large, eagerly loaded MCP surfaces have real token and reliability cost
- CLI is the better default when a strong CLI already exists
- MCP needs filtering, deferred loading, or gateway patterns to stay competitive for developer tooling

<!-- src: audit-agentic-mcp/references/patterns/mcp-vs-cli.md#10.3 Practitioner signal from Reddit -->
### Practitioner signal from Reddit

Across the Reddit threads reviewed on April 15, 2026:

- Pro-CLI themes: better debugging, lower token cost, stronger results for mature CLIs in coding workflows.
- Pro-MCP themes: OAuth and per-user access, customer-facing and non-technical surfaces, stateful tools and reusable connectors.
- Complaints about MCP: auth drift, timeouts, schema bloat, low-quality community servers.
- Complaints about CLI: permission friction, quoting and shell expansion, broader local blast radius without strong controls.

Representative threads: r/AI_Agents "The Truth About MCP vs CLI" (https://www.reddit.com/r/AI_Agents/comments/1rjtp3q/the_truth_about_mcp_vs_cli/); r/ClaudeAI "Switched from MCPs to CLIs" (https://www.reddit.com/r/ClaudeAI/comments/1sakut1/switched_from_mcps_to_clis_for_claude_code_and/); r/mcp "MCP vs CLI for AI agents" (https://www.reddit.com/r/mcp/comments/1roc96a/mcp_vs_cli_for_ai_agents_when_to_use_each/); r/devsecops "Securing MCP in production" (https://www.reddit.com/r/devsecops/comments/1py3qn8/securing_mcp_in_production/).

Treat these threads as practitioner evidence, not controlled benchmarks.

## Primary docs and dated references

- Model Context Protocol architecture: https://modelcontextprotocol.io/docs/learn/architecture
- MCP transports spec, November 25, 2025: https://modelcontextprotocol.io/specification/2025-11-25/basic/transports
- MCP authorization spec, June 18, 2025: https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization
- Claude Code MCP: https://docs.anthropic.com/en/docs/claude-code/mcp
- Anthropic MCP connector: https://docs.anthropic.com/en/docs/agents-and-tools/mcp-connector
- OpenAI MCP guide: https://developers.openai.com/api/docs/mcp
- OpenAI MCP and connectors: https://developers.openai.com/api/docs/guides/tools-connectors-mcp
- Claude Code security: https://docs.anthropic.com/en/docs/claude-code/security
- Meta, "Rule of Two", October 31, 2025: https://ai.meta.com/blog/practical-ai-agent-security/
