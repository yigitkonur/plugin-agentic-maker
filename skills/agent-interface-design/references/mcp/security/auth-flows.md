# Authorization flows: first connection and step-up

> Read when: you are implementing or debugging the OAuth sequence between an MCP client, the MCP server and its authorization server, including scope escalation at runtime.

The first-connection sequence below is the reference. Any deviation means the server is either pre-spec or non-compliant. Revision-by-revision differences: [fresh/mcp-spec-revision-auth-diff.md](../../fresh/mcp-spec-revision-auth-diff.md). RFC roles: [auth-rfc-map.md](auth-rfc-map.md).

<!-- src: audit-agentic-mcp/references/patterns/auth-identity.md#3. Flow Walkthrough — First Connection (2025-11-25) -->
## First connection

1. **Unauthenticated request.** The client POSTs to `https://mcp.example.com/mcp` without `Authorization`.
2. **Server challenges.** Response: `401` with `WWW-Authenticate: Bearer resource_metadata="https://mcp.example.com/.well-known/oauth-protected-resource", scope="files:read"`.
3. **PRM fetch.** The client GETs the PRM document. Required fields: `resource`, `authorization_servers[...]`, `scopes_supported`, `bearer_methods_supported`.
4. **AS metadata fetch.** Using `authorization_servers[0]`:
   - Try RFC 8414 first: `/.well-known/oauth-authorization-server` and the path-appended form.
   - Fall back to OIDC Discovery: `/.well-known/openid-configuration` and its path-appended form.
   - **Abort if `code_challenge_methods_supported` is absent**: the AS cannot be trusted to enforce PKCE.
5. **Obtain `client_id`.** Three acceptable paths, chosen from what the AS metadata advertises (do not assume):
   - **CIMD** where the client hosts a metadata document and the AS supports it: an HTTPS URL that serves the client's JSON manifest is the `client_id`.
   - A pre-registered static `client_id` (traditional).
   - **DCR** via `/register` for clients that have neither of the above (a compatibility path: DCR is MAY in the current profile).
6. **PKCE.** `code_verifier` = 43-128 random chars; `code_challenge = BASE64URL(SHA256(code_verifier))`.
7. **Authorize.** Browser `GET /authorize?response_type=code&client_id=<id>&redirect_uri=<exact>&code_challenge=<...>&code_challenge_method=S256&state=<csrf>&scope=files:read&resource=https://mcp.example.com`.
8. **User consent.** The AS authenticates the user and shows consent; it redirects to the exact-match `redirect_uri` with `code` and `state`.
9. **Token exchange.** The client POSTs `/token` with `grant_type=authorization_code`, `code`, `code_verifier`, `redirect_uri`, `client_id`, and **`resource=https://mcp.example.com`** (MUST). The AS returns an access token with `aud="https://mcp.example.com"` plus, optionally, a rotating refresh token.
10. **Authenticated retry.** The client retries the original MCP call with `Authorization: Bearer <token>`. The server validates the signature, `iss`, `exp`, `nbf`, `aud` (exactly equal to its canonical URI) and scope, then dispatches.

> Reconciled: the sources listed DCR as the "last resort" in the flow and CIMD as the recommended default in the revision table; this file orders the paths CIMD, static, DCR and says to detect support from the AS metadata (rule and detection fields: [auth-client-identity.md](auth-client-identity.md)).

<!-- src: audit-agentic-mcp/references/patterns/auth-identity.md#4. Flow Walkthrough — Step-Up / Incremental Scope -->
## Step-up and incremental scope

Static `scopes_supported` is no longer sufficient. When a tool call needs more scope than the current token carries, the server drives the client through a new consent round.

1. The client holds a token with `scope="files:read"` and calls a tool that needs `files:write`.
2. The server returns `403 Forbidden` with `WWW-Authenticate: Bearer error="insufficient_scope", scope="files:write", resource_metadata="https://mcp.example.com/.well-known/oauth-protected-resource"`.
3. The client **MUST** treat the challenged `scope` as authoritative and ignore the PRM's static `scopes_supported`.
4. The client starts a fresh `/authorize` round with `scope=files:write`, redoes PKCE and obtains a new token.
5. The client retries the tool call with the new token.

Edge cases:

- `client_credentials` clients (machine-to-machine) that cannot run a consent UI MAY abort and surface the error.
- A server that returns `403` without `scope=` in the header violates the spec; clients must not guess scopes.
- When step-up is frequent, reconsider scope granularity: over-narrow scopes create noisy consent loops.

Sources: MCP authorization spec; WorkOS spec-update write-up; Stytch Cloudflare Workers OAuth walkthrough; Christian Posta's MCP auth step-by-step.
