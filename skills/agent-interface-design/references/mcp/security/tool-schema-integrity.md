# Protect tool descriptions: isolate, sign, verify

> Read when: your agent loads tools from more than one server, from a registry, or from a config file an attacker could write, and you need to stop poisoned descriptions.

<!-- src: audit-agentic-mcp/references/patterns/security.md#5. Prevent Cross-Tool Hijacking via Shared Context -->
## Prevent cross-tool hijacking through shared context

A malicious MCP tool can hijack legitimate tools without ever being called. The model sees all active tool descriptions at once, so a poisoned description in one tool can steer how it uses a completely separate tool.

Demonstrated attack: a "Fact of the Day" server hid an instruction in its tool description. When the user asked Claude to send an email through a separate mail MCP, Claude followed the injected instruction and forwarded sensitive data to the attacker. The malicious tool was never invoked.

Mitigations:

1. Treat tool descriptions as untrusted input. When loading tools from external MCPs, scan descriptions for suspicious instruction phrases (examples: `ignore previous`, `instead do`, `forward to`, `send to`) and refuse to load on a match.
2. Use separate contexts per MCP server. Do not mix high-trust tools (email, database, internal API) with low-trust tools (trivia, weather, third-party integrations) in the same session.
3. Per-tool allowlists: explicitly declare which tools may interact.
4. Signed manifests: verify descriptions were not tampered with between authoring and loading (next section).

```
HIGH TRUST (isolated context):     LOW TRUST (sandboxed):
  email-mcp                          trivia-mcp
  database-mcp                       weather-mcp
  internal-api-mcp                   third-party-mcp
```

The attack surface is context pollution, not code execution. Audit your active tool set the way you audit dependencies.

> Note: a phrase deny-list for tool descriptions is one layer only, since string signals are not sufficient on their own; also require full-description display, hashing and re-approval on change.

Named attacks (tool shadowing, line jumping, rug pull): `threat-deep-dives.md`. Code: `../../frameworks/mcp-python/security.md`.

Sources: Marmelab, Invariant Labs "Tool Poisoning Attacks".

<!-- src: audit-agentic-mcp/references/patterns/security.md#6. Sign and Verify Tool Schemas Before Execution -->
## Sign and verify tool schemas before execution

The vulnerability is malicious instructions in tool descriptions, not malicious code. You can write every line of a tool yourself and still be compromised if an attacker pushes a poisoned description through an external data source, config file or registry.

Threat model: tool schemas (name, description, parameters) are loaded at runtime. If any part of that pipeline is writable by an attacker (shared config repo, package registry, remote manifest), the description becomes an injection vector.

Mitigation: schema hashing plus verification on load. Sign the canonical JSON (sorted keys, compact separators) with HMAC-SHA256 using a secret from the environment (`MCP_SCHEMA_SIGNING_SECRET`); compare with a constant-time compare.

Workflow:

1. Build time: hash and sign each tool schema; store signatures in a verified manifest.
2. Load time: before registering any tool, verify its schema against the signed manifest. On mismatch log at critical level and refuse to load (raise `SchemaIntegrityError`).
3. Runtime: reject tools with missing or mismatched signatures; log and alert on failures.

What goes into the signed payload: tool name, description, parameter schemas and every annotation field (`readOnlyHint`, `destructiveHint`). An attacker flipping `destructiveHint` from `true` to `false` can bypass confirmation gates.

Code: `../../frameworks/mcp-python/security.md` (`sign_schema`, `verify_schema`). Re-approval on description change and TOFU pinning: `threat-deep-dives.md`.

Sources: Christian Schneider, "Securing MCP: a defense-first architecture guide".
