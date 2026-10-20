# Capability-gate advanced protocol features

> Read when: your server uses sampling, elicitation, roots, completions, progress or cancellation, or is moving to a stateless or serverless deployment where those silently stop working.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Advanced MCP Protocol Features -->
Twelve patterns cover sampling, elicitation, roots, completions, progress, cancellation and the `_meta` field: the parts of the spec beyond tools, resources and prompts that decide whether a server feels static or agentic. Client support is uneven. Every one of these features can be silently dropped by the client, so capability checks and graceful fallbacks are non-negotiable.

Where each one lives: sampling `protocol-sampling.md`; elicitation `protocol-elicitation.md`; roots and completion `protocol-roots-and-completion.md`; progress and cancellation `protocol-progress-and-cancellation.md`; `_meta` keys `protocol-meta-keys.md`; combining them `protocol-feature-composition.md`. Which clients support what: `../fresh/mcp-advanced-feature-support.md`. Which spec revision added what: `../fresh/mcp-advanced-feature-revisions.md`.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 1: Capability-Gate Every Advanced Feature Before Using It -->
## Inspect declared capabilities before every advanced call

Rule: never invoke `sampling/createMessage`, `elicitation/create` or `roots/list` without first inspecting the client capabilities declared at `initialize`. If the capability is absent, fall back to embedding the request in a regular tool response and let the calling agent handle it.

Most clients silently fail advanced calls (for example by returning "Method not found: sampling/createMessage"), and some feature requests were closed as not planned. A server that assumes support crashes on the majority of clients; the dated reports are in `../fresh/mcp-advanced-feature-support.md`.

Fallback behaviour: the tool returns a clearly marked text result (for example a `SAMPLING_UNAVAILABLE:` prefix) that tells the orchestrating agent what to do itself, such as "summarize this document yourself and call `save_summary` with the result", and includes the payload to work on. Code: `../frameworks/mcp-python/advanced-protocol.md`.

When to use: always, for every one of `sampling`, `elicitation`, `roots` and `completions`.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 12: Detect Stateless HTTP Mode Early — Advanced Features Silently Break Without A Session -->
## Detect stateless HTTP mode at startup

Rule: sampling, elicitation, progress and cancellation all require a persistent server-to-client channel. In stateless HTTP mode (no session ID, no SSE stream) none of them work. Detect stateless mode at server startup and either (a) disable the advanced-feature tools, or (b) raise a structured error when the client attempts to call one.

The failure mode is silent. The server issues a `sampling/createMessage` request, the client never receives it (no open SSE stream), and the tool blocks forever or times out. Teams hit this when moving to serverless deployments without realising that Streamable HTTP with sessions is required for bidirectional calls (a known FastMCP issue; see the fresh file). The error text the tool returns should say the server runs in stateless HTTP mode, cannot use sampling, and name the setting that enables sessions (`stateless_http=False`).

When to use: every server that plans to deploy behind serverless, load balancers or any architecture that might be stateless. Hosting consequences: `ops-hosting-constraints.md` and `ops-transport-selection.md`; sessionless servers can still return task IDs for long work: `ops-long-running-tasks.md`.

Sources: MCP specification (sampling, transports).
