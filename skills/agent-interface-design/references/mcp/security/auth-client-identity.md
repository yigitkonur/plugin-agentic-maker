# Establish client identity: CIMD first, DCR as fallback

> Read when: you must decide how OAuth clients identify themselves to your authorization server, or you are auditing DCR exposure and confused-deputy risk.

## Decision rule

A client follows the 2025-11-25 spec order: pre-registered client information if it has any, then Client ID Metadata Documents (CIMD, SEP-991), then Dynamic Client Registration (DCR, RFC 7591), then ask the user. Never assume which exist: read the authorization-server metadata and branch. An authorization server that wants public clients should advertise CIMD and may keep a `registration_endpoint` as the compatibility path.

```
client has pre-registered information for this server                       -> use it
else AS metadata has client_id_metadata_document_supported: true             -> client_id is the HTTPS URL of its manifest (CIMD)
else AS metadata has a registration_endpoint                                 -> POST to that URL, constrained and rate-limited (DCR)
else                                                                         -> ask the user for the client details
```

> Reconciled: the sources variously recommended CIMD over DCR, treated DCR as a last resort, or described DCR as the baseline for MCP clients; this file follows the spec's order (pre-registered, CIMD where the AS advertises it, DCR as the fallback, then the user) and says to detect support from the AS metadata.

Why CIMD: it anchors client identity to a public HTTPS URL, so the `redirect_uris` are tied to DNS and an attacker cannot forge them. The AS fetches the manifest (`client_id`, `client_name`, `redirect_uris`, optional `jwks` / `jwks_uri` for `private_key_jwt`) and MUST exact-match every `redirect_uri` against it on each authorize request. DCR is a free-for-all endpoint unless you constrain it (below). Revision history of this stance: [fresh/mcp-spec-revision-auth-diff.md](../../fresh/mcp-spec-revision-auth-diff.md).

<!-- src: audit-agentic-mcp/references/patterns/auth-identity.md#7. Attack Primitive — Confused Deputy (MCP-As-Faux-AS) -->
## Attack: confused deputy (MCP server as a fake AS)

An MCP server that also acts as an AS, accepts unauthenticated `/register`, and honours persistent IdP consent cookies can be weaponized into issuing sessions to attacker clients that impersonate the victim.

Mechanics: the attacker registers a client dynamically and crafts an `/authorize` link to the MCP server's AS. The victim clicks, the victim's IdP cookie auto-consents, the MCP server redirects a code back to the attacker's `redirect_uri`, and the attacker completes PKCE and gets a session.

Defences:

- Keep the MCP server and the AS separate; the split of resource server and AS exists for this reason.
- If separation is unavoidable, require a separate consent-cookie step that cannot be silently replayed.
- Use CIMD, which ties `redirect_uris` to DNS.
- The AS **MUST exact-match** `redirect_uri` against the fetched CIMD document.
- Use `__Host-` prefix cookies and `SameSite=Lax` at minimum.

<!-- src: audit-agentic-mcp/references/patterns/auth-identity.md#9. Attack Primitive — DCR Rug Pull And Tool Squatting -->
## Attack: DCR rug pull and tool squatting

With DCR open and unlimited, attackers register thousands of client records with plausible names, publish MCP servers whose tool descriptions change after approval, or poison a shared registry. A widely used client was publicly observed creating hundreds of thousands of DCR clients without rate limits (dated detail: [fresh/mcp-auth-incidents.md](../../fresh/mcp-auth-incidents.md)).

Defences:

- Constrain DCR registrations: force `grant_types=["authorization_code"]`, `response_types=["code"]`, `token_endpoint_auth_method="none"` for public clients, reject unknown fields, and drop requests outside an allowlisted domain.
- Rate-limit `/register` per IP and per tenant.
- Emit an admin-visible audit record for every registration and expose a revocation API.
- Prefer CIMD over DCR for new deployments: it anchors trust in DNS + HTTPS rather than an open endpoint.
- For tool definitions themselves, adopt ETDI-style signed, immutable tool schemas ([tool-schema-integrity.md](tool-schema-integrity.md) covers the signing mechanics; ETDI adds versioned tool IDs).

Sources: den.dev and Obsidian Security confused-deputy write-ups; ETDI paper; Trail of Bits MCP security-layer post; WorkOS DCR write-up.
