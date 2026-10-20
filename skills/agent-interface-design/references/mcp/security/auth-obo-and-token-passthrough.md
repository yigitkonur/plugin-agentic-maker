# Call upstream APIs on behalf of the user, never by passing the token through

> Read when: an MCP tool must call another API as the user, or you are checking that a server validates `aud` and does not forward bearer tokens.

An MCP server that forwards its own bearer token to an upstream API is indistinguishable from an attacker that replays it. The spec-level MUSTs here are non-negotiable. Code: [frameworks/mcp-python/auth-identity.md](../../frameworks/mcp-python/auth-identity.md). Tenant-level layouts built on these options: [auth-multi-tenant-patterns.md](auth-multi-tenant-patterns.md).

<!-- src: audit-agentic-mcp/references/patterns/auth-identity.md#5. Flow Walkthrough — On-Behalf-Of (OBO) For Upstream APIs -->
## On-behalf-of options

The MCP spec does not yet standardize on-behalf-of (OBO). Three patterns are in production today. Pick one; never fall back to forwarding the user's MCP token to upstream APIs.

**Option A: RFC 8693 Token Exchange (strongest).** The MCP server holds its own client credential with an internal security token service (STS). It exchanges `subject_token = user's MCP access token`, `actor_token = MCP server's own token`, `resource = upstream API`, `scope = <narrow>`. The STS returns a fresh token audienced for the upstream API with the real user as `sub`. Upstream RBAC applies to the user, not to the MCP service account.

**Option B: Identity Assertion Authorization Grant (`id-jag`) / Cross-App Access (XAA).** The enterprise IdP issues a signed assertion tying the MCP client and the upstream app, so tokens can be swapped without a second consent screen. Requires both apps connected to the same IdP with XAA enabled. (One vendor treats this as the default for enterprise MCP; see [fresh/mcp-spec-revision-auth-diff.md](../../fresh/mcp-spec-revision-auth-diff.md).)

**Option C: URL-mode elicitation (lightest).** The server returns an elicitation that points the client to an upstream OAuth URL. **Critically, the callback goes to the MCP server, not the client.** The server stores the upstream refresh token keyed by the MCP identity's `sub` and refreshes on demand. Upstream tokens never leave the trusted server. Trade-off: an extra consent screen. Mechanics of URL-mode elicitation: [../protocol-elicitation.md](../protocol-elicitation.md).

| Pattern | Best for | Key cost |
|---|---|---|
| RFC 8693 | Single enterprise, tight STS | STS infrastructure |
| `id-jag` / XAA | Multi-app enterprise SSO | Both apps on same IdP |
| URL elicitation | Consumer / indie MCP | Extra consent UI |

<!-- src: audit-agentic-mcp/references/patterns/auth-identity.md#6. Always Validate `aud` — And Never Pass Tokens Through -->
## Validate `aud` and never pass tokens through

Validate every inbound token with a library that checks signature, `iss`, `exp`, `sub` and `aud` and requires all four claims to be present; the audience is the server's canonical URI (example: `https://mcp.example.com`).

Rules:

- Audience is the MCP server's canonical URI, byte-for-byte.
- If `aud` is an array, at least one element must equal the canonical URI **and** no other element may be treated as proof.
- Never re-use a received token as `Authorization` on an outbound call; use OBO (the options above).
- Reject tokens whose `typ` or `alg` is weaker than expected (`typ != "JWT"` or unsigned `alg=none`).

<!-- src: audit-agentic-mcp/references/patterns/auth-identity.md#8. Attack Primitive — Token Audience Confusion And Passthrough -->
## Attack: token audience confusion and passthrough

The attacker coerces the MCP server into replaying its bearer token against an upstream API; the upstream observes the original user's `sub` and authorizes the call.

Defences:

- The MCP server MUST reject any token whose `aud` does not equal its own canonical URI.
- Upstream APIs MUST reject tokens whose `aud` is another service.
- Mint a fresh upstream-audienced token via RFC 8693 (Option A) or XAA (Option B); never reuse.
- Treat a "bearer token with matching `sub` but wrong `aud`" as a security incident, not a bug.

Posture across the whole server: [decisions/security-posture.md](../../decisions/security-posture.md). Sources: MCP authorization spec; Solo.io upstream-API authorization patterns; WorkOS DCR/MCP/OAuth write-up; ForgeCode spec-update write-up.
