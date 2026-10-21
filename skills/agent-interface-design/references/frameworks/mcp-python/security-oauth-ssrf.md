# Python: scope-checked token verification and SSRF guard

> Read when: you are implementing JWT audience/scope checks and an outbound-URL SSRF filter for an external-facing MCP server in Python.

Decisions, scope table and session TTLs: `../../mcp/security/oauth-scopes-ssrf-sessions.md`. Other security code: `security.md`.

<!-- src: audit-agentic-mcp/references/patterns/security.md#8. Use OAuth2 with Granular Scopes for External MCP Servers -->
## Token validation, SSRF block, session IDs

```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import SecurityScopes
from jose import JWTError, jwt

CANONICAL_URI = "https://mcp.example.com"  # this server's canonical URI, the token audience

async def verify_mcp_token(security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"], audience=CANONICAL_URI)
    except JWTError:  # bad signature, expired, or issued for another audience
        raise HTTPException(401, "Invalid token", headers={"WWW-Authenticate": 'Bearer error="invalid_token"'})
    token_scopes = set(payload.get("scope", "").split())
    for scope in security_scopes.scopes:
        if scope not in token_scopes:  # valid token, not enough scope: 403
            raise HTTPException(403, f"Missing scope: {scope}",
                                headers={"WWW-Authenticate": f'Bearer error="insufficient_scope", scope="{scope}"'})
    return payload
```

Scope design:

```
mcp:read    -> search, list, describe    mcp:write  -> create, update
mcp:delete  -> destructive (rare)        mcp:admin  -> config (never auto-granted)
```

Block SSRF to private IP ranges (external-facing MCP servers must never reach internal networks):

```python
import ipaddress
import socket
import urllib.parse

BLOCKED = ["0.0.0.0/8", "10.0.0.0/8", "100.64.0.0/10", "127.0.0.0/8", "169.254.0.0/16",
           "172.16.0.0/12", "192.168.0.0/16", "::1/128", "fc00::/7", "fe80::/10"]
BLOCKED_NETS = [ipaddress.ip_network(n) for n in BLOCKED]

def is_safe_url(url: str) -> bool:
    host = urllib.parse.urlparse(url).hostname
    try:
        infos = socket.getaddrinfo(host, None)  # every A and AAAA record
    except (socket.gaierror, TypeError):
        return False
    return not any(ipaddress.ip_address(i[4][0]) in net for i in infos for net in BLOCKED_NETS)
# DNS rebinding: connect to the address you just checked (pin it), do not resolve again.
```

Session IDs: generate with a CSPRNG (`uuid4()`), bind to user identity, rotate on privilege escalation (TTL 15 min elevated, 1 hour read-only).
