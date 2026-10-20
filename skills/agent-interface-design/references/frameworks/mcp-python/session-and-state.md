# Python: session state, success log and background tasks

> Read when: you are implementing session-scoped state, a successful-call log, or a background task tool in Python (FastMCP or the Python SDK).

Rules and tables: [ops-session-state.md](../../mcp/ops-session-state.md), [ops-success-log-and-compaction.md](../../mcp/ops-success-log-and-compaction.md), [ops-long-running-tasks.md](../../mcp/ops-long-running-tasks.md).

<!-- src: audit-agentic-mcp/references/patterns/session-and-state.md#1. Log Successful Tool Calls to Build a Learning Database -->
## Log successful calls, quote one in the error

```python
import json
from pathlib import Path

SUCCESS_LOG = Path("./successful_calls.jsonl")

@tool
def query_api(endpoint: str, params: dict) -> dict:
    try:
        result = api.call(endpoint, params)
        # Log the successful call
        SUCCESS_LOG.open("a").write(json.dumps({
            "endpoint": endpoint,
            "params": params,
            "timestamp": datetime.now().isoformat()
        }) + "\n")
        return result
    except APIError as e:
        # Find a similar successful call
        similar = find_similar_successful_call(endpoint, params)
        error_msg = f"API call failed: {e}"
        if similar:
            error_msg += (
                f"\n\nA similar successful call used these parameters:\n"
                f"{json.dumps(similar['params'], indent=2)}\n"
                f"Try adjusting your parameters to match this pattern."
            )
        return {"content": [{"type": "text", "text": error_msg}], "isError": True}
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
    Runs as a background task -- returns a task ID immediately.
    Use the task status endpoint to poll for completion."""
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

@tool
def next_page():
    global current_page
    current_page += 1  # Race condition when multiple sessions are active
    return fetch_page(current_page)
```

Good, session-scoped state:

```python
from collections import defaultdict

session_state = defaultdict(dict)

@tool
def next_page(ctx: Context):
    sid = ctx.session_id
    page = session_state[sid].get("page", 0) + 1
    session_state[sid]["page"] = page
    return fetch_page(page)

@tool
def set_preferences(ctx: Context, timezone: str, language: str):
    session_state[ctx.session_id]["prefs"] = {
        "timezone": timezone,
        "language": language
    }
    return {"status": "Preferences saved for this session."}
```
