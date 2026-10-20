# Composing progress, cancellation, sampling and elicitation

> Read when: a tool runs over five seconds, has ambiguous inputs and should not ship an API key, or you need an out-of-band OAuth step.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 11: Compose Progress + Cancellation, Sampling + Elicitation, And URL-Mode + `_meta` For Full Agentic UX -->
## Three compositions that carry most of the value

Rule: the advanced features compose. The three highest-leverage compositions:

1. **Long tool = progress + cancellation.** Read `params._meta.progressToken`; emit `notifications/progress` per chunk; check cancellation each loop; on cancel, raise and skip the response. See `protocol-progress-and-cancellation.md`.
2. **Clarify then execute = elicitation + sampling.** The tool receives an ambiguous goal, calls `elicitation/create` to pick specifics, then `sampling/createMessage` to generate the artifact on the client's LLM. No server API key required. See `protocol-elicitation.md` and `protocol-sampling.md`.
3. **Out-of-band OAuth = URL-mode elicitation + `_meta` + progress.** The tool raises `UrlElicitationRequiredError`, the client opens the browser, the OAuth backend completes, and the server emits `notifications/progress` carrying `_meta.io.modelcontextprotocol/auth-state: "granted"` to signal readiness. See `protocol-meta-keys.md`.

The worked example is a `research` tool: (1) elicit research preferences and return "cancelled" unless the action is `accept`; (2) loop over sources, checking cancellation and reporting progress `i+1` of N with the source name; (3) synthesize through sampling with `max_tokens=2048`. Code: `../frameworks/mcp-python/advanced-protocol.md`.

> Unresolved: composition 3 uses a key under the reserved `io.modelcontextprotocol` prefix, while `protocol-meta-keys.md` says that prefix is reserved for the spec and custom keys must be reverse-DNS under your own domain. The source gives no ruling; for a custom signal prefer a key such as `com.example/auth-state`.

When to use: any agentic tool that runs more than 5 seconds, has ambiguous inputs, and should avoid shipping an API key.

When NOT to use: the target client does not advertise all three capabilities. Degrade per `protocol-capability-gating.md` rather than fail.

Sources: MCP specification (sampling, elicitation).
