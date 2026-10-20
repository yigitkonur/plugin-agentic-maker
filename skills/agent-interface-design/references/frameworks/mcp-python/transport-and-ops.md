# Python: stderr logging, transport selection, error-safe handlers, lazy auth

> Read when: you are writing the Python side of an MCP server's logging, transport setup, hot-reload loop, error handling or token checks.

Rules: [ops-stdio-hygiene.md](../../mcp/ops-stdio-hygiene.md), [ops-transport-selection.md](../../mcp/ops-transport-selection.md), [ops-dev-loop.md](../../mcp/ops-dev-loop.md), [ops-observability.md](../../mcp/ops-observability.md), [ops-server-resilience.md](../../mcp/ops-server-resilience.md).

<!-- src: audit-agentic-mcp/references/patterns/transport-and-ops.md#1. Keep stdout Pure JSON-RPC -- All Logs to stderr -->
## Send all logging to stderr

```python
import logging
import sys

# Configure all logging to stderr
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    stream=sys.stderr
)

logger = logging.getLogger(__name__)

# NEVER use print() in an MCP server
# Use logger instead
logger.info("Server started")
logger.error("Tool failed", exc_info=True)
```

Node.js equivalent (never `console.log()`; see the [typescript file](../mcp-ts/transport-and-ops.md)).

<!-- src: audit-agentic-mcp/references/patterns/transport-and-ops.md#2. Use Streamable HTTP, Not Deprecated SSE -->
## Select the transport

```python
from fastmcp import FastMCP

mcp = FastMCP("My Server")

# For local development
if __name__ == "__main__":
    mcp.run(transport="stdio")

# For remote deployment
# mcp.run(transport="http", host="0.0.0.0", port=8000)
```

<!-- src: audit-agentic-mcp/references/patterns/transport-and-ops.md#3. Use Hot Reload During Development -->
## Hot reload and direct-call tests (FastMCP)

```bash
# Auto-restarts on file changes and opens MCP Inspector
fastmcp dev inspector server.py
```

Other commands: `fastmcp dev` is the development server with hot reload. In FastMCP 3.0 (verify against the installed version, see ../../fresh/mcp-client-and-sdk-quirks.md), tool decorators return the original function for direct testing:

```python
@mcp.tool()
def add(a: int, b: int) -> int:
    return a + b

# Direct call in tests (no MCP overhead)
result = add(2, 3)

# Remote call via MCP
await client.call_tool("add", {"a": 2, "b": 3})
```

<!-- src: audit-agentic-mcp/references/patterns/transport-and-ops.md#4. Add Structured Observability from Day One -->
## Structured log line and health route

```python
import json
import sys
from datetime import datetime, timezone

def log_tool_call(tool_name: str, params: dict, result: dict, duration_ms: float):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": "INFO",
        "event": "tool_call",
        "tool": tool_name,
        "params": {k: v for k, v in params.items() if k not in SENSITIVE_FIELDS},
        "success": not result.get("isError", False),
        "duration_ms": duration_ms,
        "tokens_estimate": len(json.dumps(result)) // 4
    }
    print(json.dumps(entry), file=sys.stderr)
```

```python
@app.get("/health")
def health():
    checks = {
        "database": check_db_connection(),
        "cache": check_redis(),
        "external_api": check_api_reachable()
    }
    healthy = all(checks.values())
    return {"status": "healthy" if healthy else "degraded", "checks": checks}
```

<!-- src: audit-agentic-mcp/references/patterns/transport-and-ops.md#5. Never Call process.exit() or sys.exit() Inside Tool Handlers -->
## Return a structured error instead of exiting

Wrong, kills the server:

```python
@mcp.tool(name="validate_config")
async def validate_config(path: str) -> list[TextContent]:
    config = load_config(path)
    if not config:
        print("Fatal: invalid config", file=sys.stderr)
        sys.exit(1)  # Server dies. All tools gone.
```

Right, structured error and the server stays alive:

```python
from mcp.server.fastmcp.exceptions import ToolError  # fastmcp package: from fastmcp.exceptions import ToolError

@mcp.tool(name="validate_config")
async def validate_config(path: str) -> str:
    config = load_config(path)
    if not config:
        # raising ToolError makes FastMCP send an error result (isError: true)
        raise ToolError(
            f"Config at '{path}' is invalid or missing. "
            f"Expected YAML with keys: host, port, db_name."
        )
    return "Config is valid."
```

Also catch unhandled exceptions in tool handlers:

```python
async def safe_handler(func, **kwargs):
    try:
        return await func(**kwargs)
    except Exception as e:
        raise ToolError(f"Internal error: {type(e).__name__}: {e}") from e  # error result, logged as failure
```

<!-- src: audit-agentic-mcp/references/patterns/transport-and-ops.md#7. Validate Authentication Tokens at Execution Time, Not Startup -->
## Validate the token inside the handler

Wrong, startup validation (the server crashes if the token is bad):

```python
api_token = os.environ["API_TOKEN"]
httpx.get("https://api.example.com/me",
          headers={"Authorization": f"Bearer {api_token}"}).raise_for_status()  # -> crash
mcp = FastMCP("my-server")  # Never reached
```

Right, validate at execution time:

```python
mcp = FastMCP("my-server")

@mcp.tool(name="search_tickets")
async def search_tickets(query: str) -> str:
    api_token = os.environ.get("API_TOKEN")
    if not api_token:
        raise ToolError("API_TOKEN not set. Add it to your environment and restart the server.")

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.example.com/tickets",
                params={"q": query},
                headers={"Authorization": f"Bearer {api_token}"},
            )
            resp.raise_for_status()
            return resp.text
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise ToolError("Token expired or invalid. Re-authenticate at https://example.com/settings/tokens")
        raise
```
