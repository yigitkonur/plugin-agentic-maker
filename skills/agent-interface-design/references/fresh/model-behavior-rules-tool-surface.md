---
as_of: 2026-04-14
verify_before_citing: true
---

# Model rules for the tool surface: tool cap, polymorphism, schema portability

> Read when: you size the active tool set for several vendors' models or make schemas portable across Gemini, Mistral, Qwen, Llama 4, OpenAI and DeepSeek. This is rules 1, 2, 6, 13 of the adjustment rules.

Code: `frameworks/mcp-model-portability-snippets.md`. Conflicts between these rules (`oneOf` use, enum size, tool cap) are tabulated in `model-behavior.md`; core stance in `decisions/tool-count.md` and `mcp/schemas-*`.

<!-- src: audit-agentic-mcp/references/patterns/model-behavior.md#Adjustment Rules for MCP Server Authors -->
## Adjustment rules for MCP server authors

Numbered rules, each with the rule, the quantitative why, and a source. They change what an audit should recommend in 2025/2026. The other rules: `model-behavior-rules-vendor-idioms.md` (3, 4, 5, 11), `model-behavior-rules-context-and-runtime.md` (7, 8, 9, 12), `model-behavior-cost-and-tiers.md` (10).

<!-- src: audit-agentic-mcp/references/patterns/model-behavior.md#Pattern 1: Cap active tools at ≤20 regardless of vendor -->
## Rule 1: Cap active tools at 20 or fewer regardless of vendor

OpenAI's function-calling guide says "aim for fewer than 20 functions at any one time"; Google's Gemini docs recommend 10-20; Microsoft Research (Sep 2025) measured up to 85% accuracy loss from tool-space interference at larger surfaces. The old "Claude can do 30" rule no longer reflects vendor guidance or empirical degradation.

On a large MCP surface:

- Partition tools across scoped MCP servers (one per intent cluster).
- Filter tools per request based on the stated goal.
- Use an advisor/executor split: Claude Opus 4.5 or Gemini 3 Pro picks the workflow; a cheaper model (Haiku 4.5, GPT-5 mini, Gemini 2.5 Flash) executes it with only the filtered subset.

Source: platform.openai.com/docs/guides/function-calling, ai.google.dev/gemini-api/docs/function-calling, Klavis AI 2025-10-25 citing Microsoft Research.

<!-- src: audit-agentic-mcp/references/patterns/model-behavior.md#Pattern 2: For Gemini, emit `oneOf` not `anyOf`, and flatten nesting to ≤3 levels -->
## Rule 2: For Gemini, emit `oneOf` not `anyOf`, and flatten nesting to 3 levels or fewer

Gemini silently rejects `anyOf` and `$ref` in function calling, and API calls fail on deeply nested schemas. The Composio tool-schema flattening technique delivered +47% tool-calling improvement on Gemini in Microsoft Research's tests. Any `z.union()` in Zod input types breaks on Gemini: migrate to `z.discriminatedUnion()` (which emits `oneOf`) before shipping to Gemini clients.

Source: ai.google.dev/gemini-api/docs/function-calling; colinhacks/zod #5807 (2026-03); Composio flattening cited in Microsoft Research / Klavis analysis.

<!-- src: audit-agentic-mcp/references/patterns/model-behavior.md#Pattern 6: Treat `$ref`, `oneOf`/`anyOf`, and recursive schemas as hostile terrain -->
## Rule 6: Treat `$ref`, `oneOf`/`anyOf`, and recursive schemas as hostile terrain

Only OpenAI strict and DeepSeek reliably handle polymorphic JSON Schema features. Everyone else either rejects or silently degrades. Author tools in "lowest common denominator JSON Schema" (`type`/`properties`/`required`/`enum`/`description`/`format` only), and opt into `oneOf`/`$ref` only on an OpenAI-only or DeepSeek-only code path.

Portability test (code in the snippets file) flags: `anyOf` (breaks Gemini, Mistral, Llama 4); `$ref` (breaks Gemini, Mistral, Qwen 3); nesting deeper than 3 (breaks Gemini); an `enum` with more than 20 values (degrades all non-Claude models; a model-specific report, not a core threshold).

Source: per-family notes in `model-behavior-idioms.md`; cross-model testing in r/mcp and Klavis AI 2025-10-25.

<!-- src: audit-agentic-mcp/references/patterns/model-behavior.md#Pattern 13: For schema polymorphism, prefer `action` enums over `oneOf` -->
## Rule 13: For schema polymorphism, prefer `action` enums over `oneOf`

Gemini, Mistral, Qwen, and Llama 4 all have weak or missing polymorphic-schema support. The action-routed facade (combined CRUD, `mcp/design-*`) is the portable substitute for `oneOf`: one tool, one `action` enum, branch server-side. Keep `oneOf` only where you are OpenAI-strict or DeepSeek exclusive.
