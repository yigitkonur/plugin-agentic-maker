# Python: session state, success log and background tasks

> Read when: you are implementing session-scoped state, a successful-call log, or a background task tool in Python (FastMCP or the Python SDK).

Rules and tables: [ops-session-state.md](../../mcp/ops-session-state.md), [ops-success-log-and-compaction.md](../../mcp/ops-success-log-and-compaction.md), [ops-long-running-tasks.md](../../mcp/ops-long-running-tasks.md).

<!-- src: audit-agentic-mcp/references/patterns/session-and-state.md#1. Log Successful Tool Calls to Build a Learning Database -->
## Log successful calls, quote one in the error

```python
import json
from datetime import datetime
from pathlib import Path
from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError

mcp = FastMCP("State Server")
SUCCESS_LOG = Path("./successful_calls.jsonl")

@mcp.tool()
def query_api(endpoint: str, params: dict) -> dict:
    try:
        result = api.call(endpoint, params)
        # Log the successful call
        SUCCESS_LOG.open("a").write(json.dumps({
            "endpoint": endpoint,
            "param_names": sorted(params),  # names only: raw values may hold PII
            "timestamp": datetime.now().isoformat()
        }) + "\n")
        return result
    except APIError as e:
        # Find a similar successful call
        similar = find_similar_successful_call(endpoint, params)
        error_msg = f"API call failed: {e}"
        if similar:
            error_msg += (
                f"\n\nA similar successful call used these parameter names: "
                f"{similar['param_names']}\n"
                f"Try adjusting your parameters to match this pattern."
            )
        raise ToolError(error_msg)  # error result, not a returned dict
```

<!-- src: audit-agentic-mcp/references/patterns/session-and-state.md#2. Return Task IDs for Long-Running Operations -->
## Background task tool (FastMCP)

```python
from fastmcp import FastMCP
from fastmcp.server.tasks import TaskConfig

mcp = FastMCP("Report Server")

@mcp.tool(task=True)  # Decorator-based API -- runs as a background task
async def generate_report(data_id: str) -> dict:
    """Generate a comprehensive data report.
    Runs as a background task: the client gets a task handle immediately
    and polls the task status endpoint; this function returns the finished result."""
    # Long-running work happens here; FastMCP handles the task lifecycle
    report = await build_report(data_id)
    return {
        "status": "completed",
        "result": report,
        "message": f"Report for '{data_id}' is ready."
    }

# For more control, use TaskConfig:
# @mcp.tool(task=TaskConfig(mode="required"))
# async def heavy_analysis(data_id: str) -> dict: ...
```

<!-- src: audit-agentic-mcp/references/patterns/session-and-state.md#3. Scope State to Session, Not Global Variables -->
## Session-scoped state

Bad, global state shared across all sessions:

```python
# Global state - shared across all sessions
current_page = 0
auth_token = None

@mcp.tool()
def next_page():
    global current_page
    current_page += 1  # Race condition when multiple sessions are active
    return fetch_page(current_page)
```

Good, session-scoped state:

```python
from collections import defaultdict

session_state = defaultdict(dict)

@mcp.tool()
def next_page(ctx: Context):
    sid = ctx.session_id
    page = session_state[sid].get("page", 0) + 1
    session_state[sid]["page"] = page
    return fetch_page(page)

@mcp.tool()
def set_preferences(ctx: Context, timezone: str, language: str):
    session_state[ctx.session_id]["prefs"] = {
        "timezone": timezone,
        "language": language
    }
    return {"status": "Preferences saved for this session."}
```
