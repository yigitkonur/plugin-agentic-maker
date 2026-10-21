# Map an MCP integration against injection surfaces and supply-chain sources

> Read when: you are auditing an MCP integration end to end and need to check every route by which attacker text or a malicious package can reach the model.

<!-- src: audit-agentic-mcp/references/patterns/threat-catalog.md#2. Prompt-Injection Attack Class — Attacker Delivery Surfaces -->
## Prompt-injection delivery surfaces

The injection vectors in `threat-catalog.md` all land payloads in model context. Map every MCP integration you audit against these six surfaces and check that each has a mitigation:

1. Tool description (TPA, line jumping, rug pull). Display the full description in the UI at approval time. Re-approve on any mutation.
2. Other schema fields (FSP). Sanitize `parameter.description`, enum labels, `default`, `examples`, `title`.
3. Tool output (ATPA). Sanitize before the model sees it. A tool response is untrusted data, not instructions.
4. External data read by a tool (XPIA). Issues, emails, pages, files, messages: treat as red/untrusted. Use "MCP colors" to keep red tools out of contexts with blue tools.
5. Sampling requests/responses (covert invocation, conversation hijack, resource theft). Gate each sampling request; strip instruction-like patterns from responses (`../protocol-sampling.md`).
6. Elicitation prompts (phishing). Enforce the spec `MUST NOT` for secrets in form mode (URL mode is for those); label the server identity clearly (`../protocol-elicitation.md`).

Defender's rule of thumb: every piece of text that reaches the model from an MCP server is user-input-equivalent. Apply the same guardrails you apply to untrusted form fields. Steering text in tool output is a lever and the same channel is an attack surface; the bridge (namespaced guidance plus an `allowed_next_tools` list) is in `../../decisions/steering-contract.md`.

Attribution and dates for the rule of thumb: `../../fresh/mcp-threat-attack-sources.md`.

<!-- src: audit-agentic-mcp/references/patterns/threat-catalog.md#3. Supply-Chain Attack Class — Where the Malicious Package Comes From -->
## Supply-chain sources

Typosquatting and post-approval tampering dominate real-world compromises.

- npm typosquats: a package that silently BCC'd every outbound email to an attacker address after a later release; hundreds of weekly downloads before discovery.
- Registry lookalikes: a large fraction of servers in surveyed MCP registries were lookalikes; common tricks include case-flip (`hubspot` vs `HubSpot`), swap-homoglyph and missing-dash.
- GitHub typosquat: `acitons/artifact` vs `actions/artifact`. Moderated registries with a `verified` property are the primary defense.
- Post-approval mutation (rug pull): a server approved on day 1 ships a malicious description on day 30. Pin description hashes and force re-approval on change.

Defender actions:

- Require a signed software-statement JWT for any server publishing to a managed registry.
- Pin to a commit SHA in the client config (`claude_desktop_config.json` / `mcp.json`).
- Disable auto-update.
- Run a supply-chain scanner on the installed set weekly.

Incident figures, versions and scanner names: `../../fresh/mcp-threat-attack-sources.md`, `../../fresh/mcp-red-team-case-studies.md`, `../../fresh/mcp-defense-tooling.md`.
