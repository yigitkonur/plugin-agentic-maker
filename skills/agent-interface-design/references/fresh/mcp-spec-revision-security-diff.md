---
as_of: 2025-11-25
verify_before_citing: true
---
# MCP spec revisions: what each added for security

> Read when: you need to know which MCP spec revision introduced a security control, or whether a client or server written for an older revision lacks it.

<!-- src: audit-agentic-mcp/references/patterns/threat-catalog.md#7. Spec-Revision Security Diff (what each MCP spec version added) -->
## Security diff by revision

- 2024-11-05: no auth framework. No protocol mitigations for the attacks in `../mcp/security/threat-catalog.md`.
- 2025-03-26: Streamable HTTP + optional OAuth 2.1. Still vulnerable to poisoning / line jumping / rug pull; none addressed at protocol level.
- 2025-06-18: MCP servers re-framed as OAuth 2.0 Resource Servers; `resource` parameter (RFC 8707) required; Security Considerations + Best Practices pages added; Elicitation introduced (creates new attack surface, catalog row 11); `_meta` added; batching removed; `MCP-Protocol-Version` header mandatory.
- 2025-11-25: OpenID Connect Discovery 1.0; incremental scope consent via `WWW-Authenticate`; CIMD (SEP-991) recommended over DCR; HTTP 403 on invalid `Origin` (DNS-rebinding hardening); RFC 9728 alignment with `.well-known` fallback; Tasks + URL Mode Elicitation + Default scopes + Cross App Access + Sampling with Tools; updated Security Best Practices.
- Not yet protocol-level: tool poisoning, line jumping, rug pull, FSP, ATPA, cross-server shadowing and toxic flows remain client-implementation responsibility. The protocol does not force clients to re-approve on description change or to render full schemas at approval time.

The auth-specific revision table is in `mcp-spec-revision-auth-diff.md`. Controls that depend on a revision (checklist items 24 and 25): `../mcp/security/threat-audit-checklist.md`.

> Note: prefer Client ID Metadata Documents (CIMD) where the client supports them, keep Dynamic Client Registration (DCR) for clients without them, and never assume either: detect support from the authorization-server metadata (see ../mcp/security/auth-client-identity.md).
