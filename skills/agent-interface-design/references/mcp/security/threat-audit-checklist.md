# MCP security audit checklist: 36 binary items

> Read when: you are about to ship or approve a new MCP integration and need a yes/no review, top to bottom.

<!-- src: audit-agentic-mcp/references/patterns/threat-catalog.md#8. Audit Checklist (30+ binary items) -->
## Audit checklist

Every item is yes/no. Work top to bottom before shipping a new MCP integration. There are 36 items (the source heading said "30+"). Authorization detail lives in the auth files (`auth-audit-checklist.md`, `auth-flows.md`, `auth-client-identity.md`); keep these binary checks here.

> Reconciled: the sources variously recommended CIMD over DCR or treated DCR as the baseline; this file prefers Client ID Metadata Documents where the client supports them, keeps Dynamic Client Registration for clients without them, and never assumes either: detect support from the authorization-server metadata (see auth-client-identity.md).

**Trust and supply chain**

1. Is every installed MCP server pinned to a specific version / commit hash?
2. Is auto-update disabled for MCP servers?
3. Are tool descriptions hashed and re-approval required on change (TOFU)?
4. Are third-party servers installed only from moderated / verified registries?
5. Has the server package name been checked for typosquatting (case, punctuation, homoglyphs)?
6. Is the server code reviewed / signed before being enabled?
7. Are untrusted servers run in a sandbox, separate process, or container?

**Tool metadata hygiene**

8. Are all schema fields (not just `description`) treated as untrusted (FSP)?
9. Is tool *output* sanitized / filtered before entering model context (ATPA)?
10. Are tools referenced by fully qualified names (`server.tool`) to prevent shadowing?
11. Are Unicode tag characters (U+E0000..U+E007F) and ANSI escape sequences stripped from descriptions and outputs?
12. Is there an explicit deny list for prompt-injection patterns (`<IMPORTANT>`, "ignore previous", "you must", "instead do")?

**Authorization**

13. Does every token include and validate an `aud` / `resource` claim (RFC 8707)?
14. Is token passthrough to upstream APIs forbidden?
15. Are refresh tokens rotated for public clients? Is PKCE required for all OAuth clients?
16. Is the DCR endpoint rate-limited and scoped to trusted `redirect_uri` patterns?
17. Has CIMD (SEP-991) been adopted where feasible?
18. Are software statements (signed JWT + JWKS) used where localhost impersonation is in scope?
19. Does the OAuth callback verify `state` bound to a server-side session?
20. Are consent cookies set with the `__Host-` prefix?
21. Are OAuth endpoints served only over HTTPS, with strict `redirect_uri` allowlisting?

**Transport and session**

22. Are session IDs generated from a CSPRNG (not pointer addresses; the predictable-session-ID class, see `../../fresh/mcp-cves.md`)?
23. Are session IDs bound to user identity, rotated, and short-lived?
24. Does Streamable HTTP return HTTP 403 on invalid `Origin` (current spec revision, see `../../fresh/mcp-spec-revision-security-diff.md`)?
25. Is `MCP-Protocol-Version` validated on every HTTP request?
26. Are messages not replayed across separate streams?

**Capability and consent**

27. Is explicit user consent required before every tool invocation?
28. Is explicit user consent required before each sampling request?
29. Are sampling requests rate-limited and monitored for token-consumption anomalies (#10)?
30. Does the server abstain from eliciting sensitive info (no passwords / SSN / financials via `elicitation/create`)?
31. Is there a deny list keeping "red" (untrusted-data-reading) tools out of the same context as "blue" (critical-action) tools?

**Input and output validation**

32. Are tool inputs validated against strict schemas (path traversal, SQLi, SSRF, cmd-injection)?
33. Are resource URIs validated against provided roots?
34. Are file paths normalized (case-insensitive on macOS/Windows, `.` and symlink resolution) before access checks (the path-normalization-bypass class, see `../../fresh/mcp-cves.md`)?

**Observability**

35. Are tool invocations, description changes, and prompt-injection alerts logged and monitored?
36. Is there a kill-switch to disable a server immediately on anomaly?

<!-- src: audit-agentic-mcp/references/patterns/threat-catalog.md#9. Routing Summary -->
## Routing

- Content sanitization, PII tokenization, HMAC schema signing, SSRF blocking and delegated-permission design: `untrusted-content-and-pii.md`, `tool-schema-integrity.md`, `least-privilege-and-confirmation.md`, `oauth-scopes-ssrf-sessions.md`.
- OAuth confused deputy, token-audience binding (RFC 8707), DCR impersonation vs CIMD, session lifecycle and token-passthrough hardening: `auth-attack-primitives.md`, `auth-client-identity.md`, `auth-obo-and-token-passthrough.md`, `auth-audit-checklist.md`.
- Injection-surface advice: `threat-delivery-surfaces.md`. Posture guidance: `../../decisions/security-posture.md`; pre-launch gate: `../../decisions/production-readiness.md`.

> Reconciled: the source routed to tool-descriptions.md, tool-responses.md and decision-trees/response-format.md, which are not part of this file set; those routes are dropped here and the injection-surface advice is kept in threat-delivery-surfaces.md.
