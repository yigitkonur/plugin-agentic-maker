# Auth audit checklist before shipping

> Read when: you are about to ship (or review) a remote MCP server and want the pass/fail list for its authorization layer.

<!-- src: audit-agentic-mcp/references/patterns/auth-identity.md#17. Audit Checklist Before Shipping -->
Run every item. Failing any single item is a spec violation or a known attack vector. The list is the composite of the current authorization profile and the attack primitives in [auth-client-identity.md](auth-client-identity.md), [auth-obo-and-token-passthrough.md](auth-obo-and-token-passthrough.md) and [auth-attack-primitives.md](auth-attack-primitives.md); the binary checks that cross over to the threat model are in [threat-audit-checklist.md](threat-audit-checklist.md).

- [ ] PRM served at `/.well-known/oauth-protected-resource` with `resource`, `authorization_servers[]`, `scopes_supported`, `bearer_methods_supported`.
- [ ] `WWW-Authenticate` challenge on 401 includes `resource_metadata=` and `scope=`.
- [ ] AS advertises either RFC 8414 or OIDC Discovery metadata; `code_challenge_methods_supported` includes `S256`.
- [ ] Client uses PKCE `S256` and aborts if the AS does not advertise it.
- [ ] Client sends `resource=<canonical MCP URI>` on both `/authorize` and `/token`.
- [ ] Server validates `aud`, `iss`, `exp`, `nbf` and the signature on every request; exact-match `aud` against the canonical URI.
- [ ] Server never forwards incoming tokens upstream; it uses RFC 8693, `id-jag`, or URL elicitation for OBO.
- [ ] Step-up path returns `403` with `error="insufficient_scope"` and the required `scope=`.
- [ ] If DCR enabled: rate-limited, constrained grant/response types, allowlisted `redirect_uris` domains, admin audit log.
- [ ] If CIMD adopted: AS validates `redirect_uris` against the fetched CIMD doc on every authorize.
- [ ] No unauthenticated `/status`, `/health`, `/metrics` leaking session or tenant data.
- [ ] Tenant binding enforced at the MCP server, not trusted to upstream.
- [ ] Tool schemas signed and verified on load (see [tool-schema-integrity.md](tool-schema-integrity.md)).
- [ ] Streamable HTTP returns `403` for invalid `Origin`.

> Reconciled: the sources split CIMD and DCR across files (CIMD "recommended", DCR "baseline"); the two conditional items above stay as written and are evaluated per deployment: decide by the rule in [auth-client-identity.md](auth-client-identity.md), not by assuming either.

Sources: composite of the current MCP authorization spec and the attack primitives; OWASP MCP Top 10.
