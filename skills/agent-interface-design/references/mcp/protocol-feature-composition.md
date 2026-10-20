# Composing progress, cancellation, sampling and elicitation

> Read when: a tool runs over five seconds, has ambiguous inputs and should not ship an API key, or you need an out-of-band OAuth step.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 11: Compose Progress + Cancellation, Sampling + Elicitation, And URL-Mode + `_meta` For Full Agentic UX -->
## Three compositions that carry most of the value

Rule: the advanced features compose. The three highest-leverage compositions:

1. **Long tool = progress + cancellation.** Read `params._meta.progressToken`; emit `notifications/progress` per chunk; check cancellation each loop; on cancel, raise and skip the response. See `protocol-progress-and-cancellation.md`.
2. **Clarify then execute = elicitation + sampling.** The tool receives an ambiguous goal, calls `elicitation/create` to pick specifics, then `sampling/createMessage` to generate the artifact on the client's LLM. No server API key required. See `protocol-elicitation.md` and `protocol-sampling.md`.
3. **Out-of-band OAuth = URL-mode elicitation + completion notification.** The tool returns `URLElicitationRequiredError` (code -32042) carrying a `url` and an `elicitationId`; the client asks the user and opens the browser; the OAuth backend completes; the server sends `notifications/elicitation/complete` with that `elicitationId`, and the client may retry the call. See `protocol-elicitation.md`.

The worked example is a `research` tool: (1) elicit research preferences and return "cancelled" unless the action is `accept`; (2) loop over sources, checking cancellation and reporting progress `i+1` of N with the source name; (3) synthesize through sampling with `max_tokens=2048`. Code: `../frameworks/mcp-python/advanced-protocol.md`.

> Note: never use a key under the reserved `io.modelcontextprotocol` prefix; `protocol-meta-keys.md` keeps it for the spec. Do not invent a progress-notification signal for URL-mode elicitation: the spec sends `notifications/elicitation/complete` with the `elicitationId` (`protocol-elicitation.md`).

When to use: any agentic tool that runs more than 5 seconds, has ambiguous inputs, and should avoid shipping an API key.

When NOT to use: the target client does not advertise all three capabilities. Degrade per `protocol-capability-gating.md` rather than fail.

Sources: MCP specification (sampling, elicitation).
