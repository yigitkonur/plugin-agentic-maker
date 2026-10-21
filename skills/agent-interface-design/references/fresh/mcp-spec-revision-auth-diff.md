---
as_of: 2025-11-25
verify_before_citing: true
---
# MCP authorization: what changed between spec revisions

> Read when: a server or client was written against `2025-06-18` or earlier and you need the exact auth differences to the `2025-11-25` revision.

Verify before citing: spec text moves; check the current authorization page. The durable rules (audience binding, no passthrough, PKCE, CIMD-first with DCR fallback) are in [../mcp/security/auth-rfc-map.md](../mcp/security/auth-rfc-map.md) and [../mcp/security/auth-client-identity.md](../mcp/security/auth-client-identity.md).

<!-- src: audit-agentic-mcp/references/patterns/auth-identity.md#MCP Auth and Identity (2025-11-25 Spec) -->
## History in one paragraph

MCP moved from "auth optional, good luck" (`2025-03-26`) to a hardened OAuth 2.1 profile (`2025-11-25`) in three revisions. The `2025-06-18` revision split the MCP server (resource server) from the authorization server, which is the structural fix for the confused-deputy class. Step 5 of the first-connection flow: in `2025-11-25` DCR was reduced from SHOULD to MAY.

<!-- src: audit-agentic-mcp/references/patterns/auth-identity.md#1. Know The Spec Diff Before You Touch Auth Code -->
## Diff table

If your server or client was written against `2025-06-18` or earlier, assume it is wrong on at least one of: AS discovery, PRM location, DCR assumptions, step-up scope, or CIMD. Audit against the diff first, then code.

| Area | 2025-06-18 | 2025-11-25 |
|---|---|---|
| AS metadata discovery | RFC 8414 only | RFC 8414 **OR** OIDC Discovery 1.0: AS MUST implement at least one; clients MUST support **both** |
| PRM discovery | `WWW-Authenticate` challenge required on 401 | Either the header OR `/.well-known/oauth-protected-resource` (SEP-985 Final, 2025-07-16) |
| DCR (RFC 7591) | SHOULD support | **MAY** support (compat only) |
| Client registration (new) | none | **CIMD (SEP-991)** recommended default: HTTPS URL as `client_id`, JSON manifest with `client_id`, `client_name`, `redirect_uris`, optional `jwks`/`jwks_uri` for `private_key_jwt` |
| PKCE | MUST per OAuth 2.1 section 7.5.2 | MUST + MUST verify AS advertises support + MUST use `S256` when capable + MUST refuse if `code_challenge_methods_supported` is absent |
| Scopes / consent | Static `scopes_supported` | **Incremental / step-up** via `WWW-Authenticate scope=`; clients MUST treat challenged scope as authoritative; runtime escalation returns **403 `error="insufficient_scope"`** |
| Resource indicator (RFC 8707) | MUST | Unchanged: still MUST |
| Audience validation | Server MUST reject tokens not audienced for itself | Unchanged |
| Token passthrough | Forbidden (MUST NOT) | Unchanged |
| Redirect URIs | HTTPS or `localhost`; exact-match pre-registered | Same + under CIMD the AS MUST validate against the fetched metadata doc |
| Invalid Origin on Streamable HTTP | none | Clarified: HTTP **403** |
| Governance | none | SDK tiering, Working Groups, formal SEP process |

Only one requirement was **relaxed**: DCR dropped from SHOULD to MAY. Everything else is additive hardening.

> Note: prefer CIMD where the client supports it and keep DCR as the fallback, deciding from the authorization-server metadata.

## Vendor notes tied to a revision

- One vendor treats the Identity Assertion Authorization Grant (`id-jag`) / Cross-App Access (XAA) as the `2025-11-25` default for enterprise MCP (WorkOS, 2025-11).
- The MCP spec does not yet standardize OBO (issue #214 closed); URL-mode elicitation is tracked in issue #1036.

## Sources

- https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization
- https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization
- https://modelcontextprotocol.io/specification/2025-11-25/changelog
- https://modelcontextprotocol.io/seps/985-align-oauth-20-protected-resource-metadata-with-rf (SEP-985 Final, 2025-07-16)
- https://workos.com/blog/mcp-2025-11-25-spec-update (2025-11)
- https://auth0.com/blog/mcp-specs-update-all-about-auth/ (June 2025)
