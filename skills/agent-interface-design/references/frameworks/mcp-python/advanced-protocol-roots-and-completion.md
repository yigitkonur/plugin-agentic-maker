# Python: roots refresh and completion handler

> Read when: you are implementing `roots/list` scoping with symlink-safe path checks or a `completion/complete` handler in a Python MCP server.

Core rules: `../../mcp/protocol-roots-and-completion.md`. Gating and fallbacks: `advanced-protocol.md`.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 6: Honor `roots/list` Instead Of Hard-Coding Workspace Paths -->
## Refresh roots and check containment

```python
import os

async def refresh_roots(ctx: Context) -> list[str]:
    caps = ctx.session.client_capabilities
    if not (caps and caps.roots):
        return [os.getcwd()]  # fallback
    resp = await ctx.session.list_roots()
    roots = []
    for r in resp.roots:
        if not str(r.uri).startswith("file://"):
            continue
        path = str(r.uri).removeprefix("file://")
        roots.append(os.path.realpath(path))
    return roots

def is_inside_roots(path: str, roots: list[str]) -> bool:
    real = os.path.realpath(path)
    return any(real == r or real.startswith(r + os.sep) for r in roots)
```

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 7: Implement `completion/complete` With Context-Aware Narrowing -->
## Context-aware completion

```python
@mcp.completion()
async def complete(ref, argument, context) -> dict:
    if ref.type == "ref/prompt" and ref.name == "code_review":
        if argument.name == "language":
            values = [l for l in LANGUAGES if l.startswith(argument.value)]
            return {"values": values[:100], "total": len(values), "hasMore": len(values) > 100}
        if argument.name == "framework":
            lang = (context.arguments or {}).get("language", "")
            values = [f for f in FRAMEWORKS_BY_LANG.get(lang, []) if f.startswith(argument.value)]
            return {"values": values[:100], "total": len(values), "hasMore": False}
    return {"values": []}
```
