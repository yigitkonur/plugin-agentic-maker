# Elicitation: clarify arguments in form mode, collect secrets in URL mode

> Read when: a tool needs more input from the user mid-call, or needs a credential, OAuth grant or payment detail.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 4: Use Elicitation To Clarify Missing Arguments, Not To Fish For Secrets -->
## Form mode for missing or confirmable arguments only

Rule: for ambiguous, missing or confirmable arguments (dates, sizes, destructive confirmations), call `elicitation/create` with a flat JSON Schema. For passwords, API keys, OAuth tokens or payment details, use URL mode (next section) instead.

Form-mode limits set by the spec: flat objects with primitive properties only (`string`, `number`, `integer`, `boolean`, plus enums); no nested objects, no arrays of objects; `string.format` limited to `email`, `uri`, `date`, `date-time`. The spec also says clients MUST NOT send passwords via form mode. In practice clients do not enforce this, so a malicious or sloppy server that requests `{"password": "string"}` becomes a credential-exfiltration surface. Revision dates: `../fresh/mcp-advanced-feature-revisions.md`.

The example offers an alternative date when a table is unavailable: a model with `checkAlternative` (bool) and `alternativeDate` (string, YYYY-MM-DD); the result `action` is `accept` (use `data`) or anything else (cancel). Code: `../frameworks/mcp-python/advanced-protocol-elicitation.md`.

When to use: clarify a missing argument (shirt size, color), confirm irreversible actions (workspace delete), gather input progressively inside one tool call, recover from validation exceptions mid-tool.

When NOT to use: requesting credentials (use URL mode); running under stateless HTTP (see `protocol-capability-gating.md`). Abuse and phishing view: `security/threat-catalog.md`. Posture: `../decisions/security-posture.md`.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 5: URL-Mode Elicitation For OAuth, Secrets, And Payments -->
## URL mode for OAuth, secrets and payments

Rule: when the tool needs the user to authenticate, grant OAuth or enter a secret or payment detail, use URL-mode elicitation. The client opens the URL in an isolated browser surface the LLM cannot observe, so tokens never enter the model context.

Form mode is inadequate for secrets because the value round-trips through the client and, in many implementations, becomes visible in the conversation. URL mode delegates the secret-handling surface to a real browser plus your OAuth or payment provider. Pair it with a backend state binding keyed to the user's OAuth `sub`: the spec MUSTs that URL-elicitation state be tied to user identity, not just session ID, to prevent session-hijack replay (binding details: `security/auth-obo-and-token-passthrough.md`).

Flow: generate an elicitation ID, store `{user: sub, status: "pending"}` server-side, call the URL elicitation with the start URL carrying `state=<id>`, let the backend complete out of band, then check status `granted` and return "connected" or "not completed". Raw SDKs raise `UrlElicitationRequiredError`. Code: `../frameworks/mcp-python/advanced-protocol-elicitation.md`.

When to use: OAuth flows, API key entry, payment confirmation, any secret-handling UX where the LLM must not see the value.

When NOT to use: simple argument clarification (form mode has lower friction); the client does not advertise `elicitation.url` in its capabilities (support was very limited at the survey date, see `../fresh/mcp-advanced-feature-support.md`).

Sources: MCP specification (elicitation, changelog).
