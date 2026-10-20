# Multi-tenant SaaS auth: token exchange or URL-mode elicitation

> Read when: you are choosing how a multi-tenant MCP service obtains upstream credentials for each user, and need a reference layout for either choice.

Two reference layouts for the OBO options in [auth-obo-and-token-passthrough.md](auth-obo-and-token-passthrough.md). Pick A when you operate (or can add) an internal STS; pick B when you do not. Code sketches: [frameworks/mcp-python/auth-identity.md](../../frameworks/mcp-python/auth-identity.md) (A) and [frameworks/mcp-ts/auth-identity.md](../../frameworks/mcp-ts/auth-identity.md) (B). Per-tenant enforcement rules: [auth-attack-primitives.md](auth-attack-primitives.md).

<!-- src: audit-agentic-mcp/references/patterns/auth-identity.md#14. Multi-Tenant SaaS Reference Pattern A — Separate AS With Token Exchange -->
## Pattern A: separate AS with token exchange

The recommended default for SaaS offering MCP to enterprise customers. Roles are clearly separated, and upstream RBAC uses the real user identity.

```
[User] ──SSO──▶ [IdP]
    │
    ▼
[MCP Client]
    │  Bearer(aud=mcp.saas.com, sub=user@co)
    ▼
[MCP Server] ── RFC 8693 token exchange ──▶ [Internal STS]
    │                                            │
    │                                            ▼  mints aud=api.upstream.com, sub=user@co
    ▼
[Upstream SaaS API]  ← RBAC on real user subject, not service account
```

Scope design:

```
mcp:tools               # present to MCP server
mcp:read, mcp:write     # enforced at MCP server
upstream:leads.read     # only on the exchanged token, aud=api.upstream.com
upstream:leads.write    # only on the exchanged token
```

Config sketch: a tool takes the caller's MCP token (`aud=mcp.saas.com`), calls the STS `exchange` with `subject_token`, `actor_token` (the service actor), `audience="https://api.upstream.com"` and `scope="upstream:leads.read"`, then calls the upstream with the returned access token.

<!-- src: audit-agentic-mcp/references/patterns/auth-identity.md#15. Multi-Tenant SaaS Reference Pattern B — URL-Mode Elicitation -->
## Pattern B: URL-mode elicitation

A lighter pattern for consumer and indie MCP, or when the SaaS does not operate an STS. Upstream OAuth is completed inside the MCP server's trust boundary; upstream tokens never touch the client.

```
[User] ──Bearer(aud=mcp.saas.com)──▶ [MCP Server]
                                          │
                   tool call needs upstream (no upstream creds yet)
                                          │
                                          ▼
            Server returns elicitation { kind: "url", url: "https://mcp.saas.com/connect/github?state=..." }
                                          │
                User browser opens URL; upstream OAuth completes
                                          │
                 Callback → https://mcp.saas.com/connect/github/callback
                                          │
             Server stores upstream refresh token in KV keyed by MCP `sub`
                                          │
                          Retry tool call — now succeeds
```

Config sketch: on callback, store `{ refresh_token, aud: "api.github.com", scopes }` in a key-value store under `github:<mcpSub>`; on later tool calls load it, refresh the upstream access token, then call the upstream.

Trade-offs: one extra consent screen; simpler than an STS; upstream tokens never leave the server. Preferred for indie / consumer MCP. URL-mode mechanics and the user-identity binding of the elicitation state: [../protocol-elicitation.md](../protocol-elicitation.md).

Sources: Solo.io upstream-API authorization patterns; Christian Posta's MCP auth step-by-step; MCP URL-mode elicitation proposal; Upstash Context7 OAuth write-up.
