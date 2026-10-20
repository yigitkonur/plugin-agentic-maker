---
as_of: 2025-11-25
verify_before_citing: true
---
# Which MCP spec revision introduced each advanced feature

> Read when: you need to know whether an advanced MCP feature or field exists in the spec revision your client or server targets.

As stated for spec revisions 2025-06-18 and 2025-11-25). Verify against the current spec before citing. Core rules: `../mcp/protocol-capability-gating.md`, `../mcp/protocol-sampling.md`, `../mcp/protocol-elicitation.md`, `../mcp/protocol-roots-and-completion.md`, `../mcp/protocol-progress-and-cancellation.md`, `../mcp/protocol-meta-keys.md`.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 2: Use Sampling to Keep the API Key on the Client Side -->
## Sampling

- The 2025-11-25 revision added `tools` and `toolChoice` parameters to sampling, enabling server-side agent loops with standard MCP primitives (WorkOS, 2025-11).

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 3: Sampling-With-Tools Requires Matching `ToolResultContent` For Every `ToolUseContent` -->
## Sampling with tools

- The `tools: {}` capability flag is new in 2025-11-25 and absent on pre-2025-11 clients. Check `caps.sampling.tools is not None` before sending tools.
- Every `ToolUseContent` needs a matching `ToolResultContent` before the next `createMessage` (rule stated for 2025-11-25).

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 4: Use Elicitation To Clarify Missing Arguments, Not To Fish For Secrets -->
## Form-mode elicitation

- Introduced in 2025-06-18, expanded in 2025-11-25.
- Restricted by spec to flat objects with primitive properties (`string`, `number`, `integer`, `boolean`, plus enums); `string.format` limited to `email`, `uri`, `date`, `date-time`. Clients MUST NOT send passwords via form mode.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 5: URL-Mode Elicitation For OAuth, Secrets, And Payments -->
## URL-mode elicitation

- Introduced in 2025-11-25. The spec MUSTs that URL-elicitation state be tied to user identity (not just session ID).

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 6: Honor `roots/list` Instead Of Hard-Coding Workspace Paths -->
## Roots

- Source cites the 2025-06-18 roots specification; roots are `file://` only and the spec mandates validating all root URIs to prevent path traversal.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 7: Implement `completion/complete` With Context-Aware Narrowing -->
## Completion

- The 2025-11-25 `context.arguments` field lets suggestions narrow on previously selected arguments.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 9: Handle `notifications/cancelled` Cooperatively — And Never Cancel `initialize` Or Tasks -->
## Tasks and cancellation

- The 2025-11-25 Tasks primitive is cancelled with `tasks/cancel`, not `notifications/cancelled`.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 10: Namespace Custom `_meta` Keys With Reverse-DNS; Reserve Un-Namespaced For The Protocol -->
## _meta rules

- Formalised by SEP-1788 (PR #1403, 2025-11): only `progressToken` is un-namespaced; `io.modelcontextprotocol` prefix is reserved; custom keys use reverse-DNS.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 12: Detect Stateless HTTP Mode Early — Advanced Features Silently Break Without A Session -->
## Transport

- Bidirectional calls require Streamable HTTP with sessions (MCP spec 2025-11-25, basic transports).
