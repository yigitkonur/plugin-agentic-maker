# Harden an external-facing MCP server: scopes, SSRF, sessions

> Read when: you are exposing an MCP server beyond localhost and must define token validation, scope tiers, outbound-request limits and session lifetime.

<!-- src: audit-agentic-mcp/references/patterns/security.md#8. Use OAuth2 with Granular Scopes for External MCP Servers -->
## Use OAuth2 with granular scopes

For external-facing servers, implement OAuth2 with narrowly scoped permissions. Do not accept tokens not explicitly issued for your server. Start with a minimal scope baseline and request higher privileges only when a specific tool requires them.

Token validation: decode and verify the JWT signature (RS256), require `aud` to equal this server's canonical URI (example: `https://mcp.example.com`; reject a token for another audience with 401 and `WWW-Authenticate: Bearer error="invalid_token"`), then check that every scope the endpoint needs is in the token's space-separated `scope` claim (403 with `error="insufficient_scope"` and the needed `scope`, "Missing scope: ..."). The full protocol profile (RFC 9728, RFC 8707, step-up) is in `auth-flows.md` and `auth-obo-and-token-passthrough.md`.

Scope design, least privilege:

| Scope | Allows |
|---|---|
| `mcp:read` | search, list, describe |
| `mcp:write` | create, update |
| `mcp:delete` | destructive operations (rare) |
| `mcp:admin` | config; never auto-granted |

Block SSRF to private ranges. External-facing MCP servers must never reach internal networks. Resolve the hostname of any user-supplied URL and reject when the address falls in:

| Blocked CIDR |
|---|
| `10.0.0.0/8` |
| `172.16.0.0/12` |
| `192.168.0.0/16` |
| `127.0.0.0/8` |
| `169.254.0.0/16` |

Session security:

- Generate session IDs with a CSPRNG (`uuid4()`), never sequential IDs (the predictable-session-ID class is listed in `../../fresh/mcp-cves.md`).
- Bind sessions to user identity; verify on every request.
- Rotate on privilege escalation. TTL: 15 min for elevated scopes, 1 hour for read-only.

Neutral check for the rejection path:

```bash
curl -s -o /dev/null -w '%{http_code}\n' -H 'Authorization: Bearer <token-for-another-audience>' https://mcp.example.com/mcp   # expect 401
```

Code: `../../frameworks/mcp-python/security.md`. Checklist form: `threat-audit-checklist.md`.

Sources: NCC Group "5 MCP Security Tips", MCP specification security guidance.
