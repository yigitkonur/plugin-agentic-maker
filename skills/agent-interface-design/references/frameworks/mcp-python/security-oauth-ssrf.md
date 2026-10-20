# Python: scope-checked token verification and SSRF guard

> Read when: you are implementing JWT audience/scope checks and an outbound-URL SSRF filter for an external-facing MCP server in Python.

Decisions, scope table and session TTLs: `../../mcp/security/oauth-scopes-ssrf-sessions.md`. Other security code: `security.md`.

<!-- src: audit-agentic-mcp/references/patterns/security.md#8. Use OAuth2 with Granular Scopes for External MCP Servers -->
## Token validation, SSRF block, session IDs

```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import SecurityScopes

async def verify_mcp_token(security_scopes, token = Depends(oauth2_scheme)):
    payload = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])
    if payload.get("aud") != "mcp-server-prod":
        raise HTTPException(403, "Token not issued for this MCP server")
    token_scopes = set(payload.get("scope", "").split())
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(403, f"Missing scope: {scope}")
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

BLOCKED = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",
           "127.0.0.0/8", "169.254.0.0/16"]
BLOCKED_NETS = [ipaddress.ip_network(n) for n in BLOCKED]

def is_safe_url(url: str) -> bool:
    ip = ipaddress.ip_address(socket.gethostbyname(
        urllib.parse.urlparse(url).hostname))
    return not any(ip in net for net in BLOCKED_NETS)
```

Session IDs: generate with a CSPRNG (`uuid4()`), bind to user identity, rotate on privilege escalation (TTL 15 min elevated, 1 hour read-only).
