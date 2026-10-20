# Python: validate `aud` and exchange tokens for upstream calls

> Read when: you are writing the Python token-validation and token-exchange code for an MCP server; the rules are in the core auth files.

Rules: [../../mcp/security/auth-obo-and-token-passthrough.md](../../mcp/security/auth-obo-and-token-passthrough.md). Layout: [../../mcp/security/auth-multi-tenant-patterns.md](../../mcp/security/auth-multi-tenant-patterns.md).

<!-- src: audit-agentic-mcp/references/patterns/auth-identity.md#6. Always Validate `aud` — And Never Pass Tokens Through -->
## Validate the audience

```python
from jose import jwt

async def verify_mcp_token(raw_token: str) -> dict:
    payload = jwt.decode(
        raw_token,
        KEY,
        algorithms=["RS256"],
        audience="https://mcp.example.com",   # exact canonical URI
        issuer=EXPECTED_ISSUER,
        options={"require": ["aud", "iss", "exp", "sub"]},
    )
    if payload["aud"] != "https://mcp.example.com":
        raise Unauthorized("aud mismatch")
    return payload
```

<!-- src: audit-agentic-mcp/references/patterns/auth-identity.md#14. Multi-Tenant SaaS Reference Pattern A — Separate AS With Token Exchange -->
## Token exchange per tool call (FastAPI + internal STS)

```python
@tool
async def list_leads(ctx: Context) -> dict:
    mcp_token = ctx.session.raw_token            # aud=mcp.saas.com
    upstream = await sts.exchange(
        subject_token=mcp_token,
        actor_token=service_actor_token,
        audience="https://api.upstream.com",
        scope="upstream:leads.read",
    )
    return await upstream_client.list_leads(token=upstream.access_token)
```
