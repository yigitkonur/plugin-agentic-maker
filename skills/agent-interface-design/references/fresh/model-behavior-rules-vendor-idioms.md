---
as_of: 2026-04-14
verify_before_citing: true
---

# Model rules for vendor idioms: Claude caching, GPT freeform, DeepSeek batching, parallel-call bugs

> Read when: you tune an MCP integration for Claude, GPT-5, or DeepSeek, or must disable parallel tool calls on a known-buggy model/version. Rules 3, 4, 5, 11 of the adjustment rules.

Code (Claude cache block): `frameworks/mcp-model-portability-snippets.md`. Index of the other rules: `model-behavior-rules-tool-surface.md`.

<!-- src: audit-agentic-mcp/references/patterns/model-behavior.md#Pattern 3: For Claude, batch all `tool_result` blocks into ONE user message and cache tool definitions on the 1h TTL -->
## Rule 3: For Claude, batch all `tool_result` blocks into ONE user message and cache tool definitions on the 1h TTL

The single-user-message-for-parallel-results rule is a hard requirement; violating it breaks Claude's tracking of parallel tool state. Route the whole tool-definitions block (typically the biggest repeating payload in an MCP session) through the 1h prompt cache. A 5,000-token tool block priced at $3/1M input costs $0.015 uncached per request; with 1h caching it costs $0.03 once on write, then $0.0015 per hit, "roughly 83% input-cost reduction" over a multi-turn session.

> Note: from the listed prices the saving is about 71% over 10 requests ($0.15 uncached vs $0.0435 cached) and reaches 83% only near 30 requests; 83% is the multi-turn figure.

Put the tool definitions in one cached block at the top of the system/tools payload with `cache_control` `{"type": "ephemeral", "ttl": "1h"}`.

Source: platform.claude.com/docs/en/agents-and-tools/tool-use/parallel-tool-use; platform.claude.com/docs/en/build-with-claude/prompt-caching.

<!-- src: audit-agentic-mcp/references/patterns/model-behavior.md#Pattern 4: For GPT-5 + non-JSON DSLs, switch to freeform tool calling -->
## Rule 4: For GPT-5 and non-JSON DSLs, switch to freeform tool calling

Shells, SQL, regex, code blocks, and custom DSLs pay a JSON-escape tax in classic tool calls: every newline becomes `\n`, every quote `\"`, and the model often gets the escaping wrong. GPT-5's freeform tool-calling mode (2025-08-22) emits raw text payloads directly. Use it for any tool whose input is code or a DSL. For genuinely structured input, keep classic JSON but set `strict: true`, `additionalProperties: false`, and mark every parameter required (nullable type for optional).

Source: devblogs.microsoft.com/foundry/unlocking-gpt-5s-freeform-tool-calling-a-new-era-of-seamless-integration/; developers.openai.com/api/docs/guides/structured-outputs.

<!-- src: audit-agentic-mcp/references/patterns/model-behavior.md#Pattern 5: For DeepSeek, prefer "one user message → many tool calls in one assistant turn" -->
## Rule 5: For DeepSeek, prefer "one user message, many tool calls in one assistant turn"

DeepSeek's own docs mark multi-turn tool dialogues as weak. Design MCP tool sequences so the agent emits multiple `tool_calls` in a single assistant message whenever possible, then consumes all results together. Avoid long interleaved turns. Pin R1-0528 or newer; older R1 revisions have material tool-calling regressions.

Source: api-docs.deepseek.com/guides/function_calling; Fireworks 2025-02-14 template reverse-engineering post.

<!-- src: audit-agentic-mcp/references/patterns/model-behavior.md#Pattern 11: Disable parallel tool calls on known-buggy model/version pairs -->
## Rule 11: Disable parallel tool calls on known-buggy model/version pairs

- `gpt-4.1-nano-2025-04-14`: duplicate-call bug; set `parallel_tool_calls: false`.
- Claude 3.5 on older SDKs: parallel results split across messages silently drop results; upgrade to the current Anthropic SDK or disable parallel.
- Mistral Large for any workflow where ordering matters: parallel is default on; flip to `false` when steps must be sequential.
- Grok 4: undocumented parallel semantics; ship with parallel off until you have measured it yourself.

Source: platform.openai.com/docs/guides/function-calling; vendor release notes and issue trackers.
