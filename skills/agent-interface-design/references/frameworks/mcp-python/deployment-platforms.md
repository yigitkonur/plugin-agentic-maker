# Python code for remote MCP hosting platforms

> Read when: you are writing Python (FastMCP) for an MCP server on GCP Cloud Run or Modal.

Platform facts, limits and prices are in the fresh files linked per section; verify before citing.

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#13. Cloud Run MCP Servers Must Bind `host="0.0.0.0"` and Use `--no-allow-unauthenticated` -->
## Cloud Run entrypoint

Facts: `../../fresh/mcp-platform-gcp-cloud-run.md`. Bind all interfaces and read `PORT` from the environment.

```python
import os
from fastmcp import FastMCP
mcp = FastMCP("my-mcp")
mcp.run(transport="http", host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
```

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#17. Modal MCP Servers Must Set `stateless_http=True` -->
## Modal stateless app

Facts: `../../fresh/mcp-platform-modal.md`.

```python
import modal
from fastmcp import FastMCP
from fastapi import FastAPI

app = modal.App("mcp-server")
image = modal.Image.debian_slim().pip_install("fastmcp", "fastapi")
mcp = FastMCP("my-mcp")
mcp_app = mcp.http_app(path="/", stateless_http=True)  # fastmcp: ASGI app; no sessions for Modal

@mcp.tool()
async def analyze(code: str) -> str: return f"lines: {len(code.splitlines())}"

web_app = FastAPI(lifespan=mcp_app.lifespan)
web_app.mount("/mcp", mcp_app)

@app.function(image=image, gpu="H100", timeout=600)
@modal.asgi_app()
def fastapi_app(): return web_app
```
