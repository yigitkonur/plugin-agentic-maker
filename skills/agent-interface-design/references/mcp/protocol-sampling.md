# Sampling: keep the API key on the client, bound the inner loop

> Read when: a tool needs LLM reasoning mid-execution, or you are tempted to ship your own model API key with the server.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 2: Use Sampling to Keep the API Key on the Client Side -->
## Call sampling instead of embedding a model key

Rule: when a tool needs LLM reasoning mid-execution, call `sampling/createMessage` instead of shipping your own API key or HTTP client to a model provider. Inference cost, rate limits and model choice stay on the user's side.

This unlocks zero-key deployments: the server never needs a provider API key (no `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in its environment), so it can be distributed publicly, run in CI or shipped to untrusted users without credential leakage. Newer spec revisions also add `tools` and `toolChoice` parameters, enabling server-side agent loops with standard MCP primitives: a server can run a bounded inner reasoning loop entirely on the client's LLM (revision detail: `../fresh/mcp-advanced-feature-revisions.md`).

Request fields used in the example: `messages`, `system_prompt`, `model_preferences` (`hints` such as a model name, `intelligencePriority` 0.8, `speedPriority` 0.4) and `max_tokens` (512). Code: `../frameworks/mcp-python/advanced-protocol-sampling.md`.

When to use: server-side sub-reasoning (summarization, classification, ranking), multi-step agent loops within one tool call, NPC dialogue generation, or any workflow where the server would otherwise need its own API key.

When NOT to use: the client does not advertise `sampling`. Many popular coding clients did not support it at the survey date (`../fresh/mcp-advanced-feature-support.md`). Detect and fall back per `protocol-capability-gating.md`.

Security: every sampled token is paid by the user and sampling is an attack channel (covert tool invocation, conversation hijack, resource theft); see `security/threat-catalog.md` and `security/threat-audit-checklist.md`.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 3: Sampling-With-Tools Requires Matching `ToolResultContent` For Every `ToolUseContent` -->
## Answer every tool use with a matching tool result

Rule: when using sampling-with-tools to drive a multi-turn inner loop, the server MUST respond to every `ToolUseContent` returned by the client with a matching `ToolResultContent` before the next `createMessage` call. Drop one and the conversation diverges or the client errors.

- The `tools: {}` capability flag is new in the 2025-11-25 revision and absent on older clients. Check `caps.sampling.tools is not None` before sending tools.
- Wrap the inner loop in an iteration limit (typical: 5-10; the example uses `max_turns=8`) to prevent runaway cost on the user's account. Users pay for every sampled token.
- Loop shape: send messages with `tools` and `toolChoice: {"mode": "auto"}` (the client must declare `sampling.tools`); append the assistant content; on stop reason `endTurn` return the text; on `toolUse` dispatch each `tool_use` block and append one user message holding a `tool_result` for each, keyed by `toolUseId` (tool results only, no other content); after the limit raise an error.

When to use: agentic tools that need several reasoning turns (research, refactoring, planning) where the client should pay for the compute.

Sources: MCP specification (sampling), WorkOS and FastMCP sampling documentation. Code: `../frameworks/mcp-python/advanced-protocol-sampling.md`.
