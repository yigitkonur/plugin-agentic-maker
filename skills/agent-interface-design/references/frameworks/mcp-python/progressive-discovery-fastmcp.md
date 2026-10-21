# FastMCP session visibility and unlocking examples

> Read when: you are using FastMCP in Python to hide tools by default and unlock them per session.

Explanation and rules: ../../mcp/patterns-dynamic-tool-lists.md. Meta-tool and staged examples: progressive-discovery.md

## Pattern 3: Session-based unlocking (admin tools)

```python
from fastmcp import FastMCP, Context
from fastmcp.server.auth import require_scopes
# FileSystemProvider: import path per the FastMCP 3.0 providers docs (not confirmed here)

mcp = FastMCP("Enterprise Server")

# 1. Mount admin tools from a directory
admin_provider = FileSystemProvider("./admin_tools")
mcp.mount(admin_provider)

# 2. Hide them by default
mcp.disable(tags={"admin"})

# 3. Gatekeeper tool that unlocks admin tools for this session
@mcp.tool(auth=require_scopes("super-user"))
async def unlock_admin_mode(ctx: Context):
    """Authenticate and unlock administrative tools for this session.
    Requires super-user OAuth scope."""
    await ctx.enable_components(tags={"admin"})
    return "Admin mode unlocked. Now available: <names of the admin tools just enabled>."
```

FastMCP 3.0 pieces used: `Visibility Transforms` control which components are visible per session; `AuthMiddleware` gates groups of components by tag; session state tracks what each user has unlocked. The unlock tool's response should list what was just made available.

## Pattern 7: FastMCP visibility transforms

> Version note: written for FastMCP 3.0 as the source states; verify against the installed version (see ../../fresh/mcp-client-and-sdk-quirks.md).

Disable by tag (applies to every session):

```python
from fastmcp import FastMCP

mcp = FastMCP("my-server")

# Disable all tools tagged "advanced" by default
mcp.disable(tags={"advanced"})
```

Per-session override inside a tool handler:

```python
from fastmcp import FastMCP, Context

@mcp.tool(tags=["core"])
async def unlock_admin_mode(ctx: Context) -> str:
    """Unlock the advanced tools for a signed-in admin."""
    # The role comes from the verified token, never from a tool argument: the model (or an attacker) picks arguments.
    if "admin" in verified_roles(ctx):  # verified_roles: your auth layer's verified claims
        await ctx.enable_components(tags={"advanced"})
        return "Admin tools unlocked."
    return "No additional tools available for this role."
```

Disable by name:

```python
mcp.disable(names={"dangerous_tool", "debug_tool"})
```

Dynamic unlock via a context tool:

```python
@mcp.tool(tags=["core"])
async def enable_advanced_mode(ctx: Context, access_code: str) -> str:
    """Unlock advanced tools for this session. Requires a valid access code."""
    if not verify_access_code(access_code):
        return "Invalid access code."

    await ctx.enable_components(tags={"advanced"})
    return "Advanced tools unlocked. Available: analyze_deep, export_bulk, admin_override."
```

Layer priority: global transforms -> session transforms -> tool-level annotations. Later layers override earlier ones, so a session transform can re-enable a tool that a global transform hid. Without session-scoped visibility you must re-register tools (which invalidates the prefix cache) or run separate server instances per user tier.
