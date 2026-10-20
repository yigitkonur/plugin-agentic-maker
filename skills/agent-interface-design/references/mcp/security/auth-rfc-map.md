# Map every MCP auth behaviour to the RFC that governs it

> Read when: you are reviewing or building the authorization layer of a remote MCP server and need to know which standard each behaviour comes from.

<!-- src: audit-agentic-mcp/references/patterns/auth-identity.md#MCP Auth and Identity (2025-11-25 Spec) -->
This file and its siblings cover protocol-level authorization for remote MCP servers and continue the generic advice in [oauth-scopes-ssrf-sessions.md](oauth-scopes-ssrf-sessions.md) (prompt injection, tool hijacking, PII and SSRF live in the other `security/` files). Assume OAuth 2.1, RFC 9728 Protected Resource Metadata (PRM), RFC 8707 resource indicators, RFC 8414 authorization-server (AS) metadata, OpenID Connect (OIDC) Discovery 1.0 and the Client ID Metadata Documents (CIMD) draft.

MCP moved from "auth optional, good luck" to a hardened OAuth 2.1 profile over three spec revisions (what each revision changed: [fresh/mcp-spec-revision-auth-diff.md](../../fresh/mcp-spec-revision-auth-diff.md)). Three invariants now drive every auth pattern:

- **Every token has an audience.**
- **Every client has a verifiable identity.**
- **MCP servers never forward user tokens upstream.**

Next: the first-connection and step-up sequences are in [auth-flows.md](auth-flows.md); upstream calls in [auth-obo-and-token-passthrough.md](auth-obo-and-token-passthrough.md); client identity in [auth-client-identity.md](auth-client-identity.md); the pre-ship list in [auth-audit-checklist.md](auth-audit-checklist.md).

<!-- src: audit-agentic-mcp/references/patterns/auth-identity.md#2. Map Every MCP Behavior To The RFC That Governs It -->
## RFC compliance table

Tick off this table before touching anything else. Non-compliance almost always comes from missing one of these, not from implementing something exotic.

| RFC / Spec | Role in MCP | Who must implement |
|---|---|---|
| RFC 6749 OAuth 2.0 | Baseline; superseded within MCP by OAuth 2.1 | AS + clients |
| OAuth 2.1 (draft) | Auth-code + PKCE only: **no implicit, no ROPC**; short-lived access tokens; rotating refresh tokens for public clients | AS + clients |
| RFC 7591 DCR | Runtime client registration. **MAY** in the current profile (compatibility only) | AS (optional) + clients (fallback) |
| RFC 7592 DCR Management | Update/delete registrations | AS |
| RFC 8414 AS Metadata | `/.well-known/oauth-authorization-server[/path]` | AS (MUST offer this or OIDC) + clients (MUST support) |
| OIDC Discovery 1.0 | `/.well-known/openid-configuration[/path]`, the alternate AS discovery | AS (MUST offer this or 8414) + clients (MUST support both) |
| RFC 9728 Protected Resource Metadata | `/.well-known/oauth-protected-resource` at the MCP server; declares `resource` and `authorization_servers` (required) and optionally `scopes_supported`, `bearer_methods_supported` | MCP server (MUST) + clients (MUST consume) |
| RFC 8707 Resource Indicators | `resource=` on `/authorize` and `/token`: canonical URI of the MCP server; binds the `aud` claim | Client (MUST send) + AS (SHOULD audience-restrict) + MCP server (MUST reject non-matching `aud`) |
| RFC 6750 Bearer Tokens | `Authorization: Bearer <token>`; `WWW-Authenticate` challenge with `error=`, `scope=`, `resource_metadata=` | Client + MCP server |
| RFC 8693 Token Exchange | OBO pattern: `subject_token` + `actor_token` gives an upstream-audienced token. Not in the MCP spec, but commonly used by servers | MCP server + internal STS |
| CIMD I-D (SEP-991) | URL-as-`client_id`; JSON manifest hosted by the client at an HTTPS URL; optional `jwks` for `private_key_jwt` | Clients (SHOULD host) + AS (SHOULD fetch, MUST validate redirects against it) |

> Reconciled: the sources gave CIMD as the recommended default in one place and DCR as the baseline in others; this file prefers CIMD where the client supports it, keeps DCR for clients without it, and never assumes either (decision rule: [auth-client-identity.md](auth-client-identity.md)).

Sources: IETF RFCs 9728, 8707, 8414, 7591, 8693, 6749; Auth0 MCP spec update write-up.
