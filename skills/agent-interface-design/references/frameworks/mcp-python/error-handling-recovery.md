# Python MCP loop breaker and normalized-input examples

> Read when: you are writing a Python MCP server that must stop identical retry loops or echo normalized inputs back to the agent.

Explanation and rules: ../../mcp/errors-loop-breaker.md and ../../mcp/errors-framing-and-recovery.md. Other error examples: error-handling.md

## Pattern 8: Hash-based loop breaker

```python
import hashlib
from collections import defaultdict
from time import time

class LoopBreaker:
    def __init__(self, max_repeats=3, window_seconds=120):
        self.max_repeats = max_repeats
        self.window = window_seconds
        self.seen: dict[str, list[float]] = defaultdict(list)

    def check(self, tool_name: str, params: dict) -> str | None:
        state = hashlib.sha256(
            f"{tool_name}:{sorted(params.items())}".encode()
        ).hexdigest()[:16]

        now = time()
        # Prune old entries outside the window
        self.seen[state] = [t for t in self.seen[state] if now - t < self.window]
        self.seen[state].append(now)

        if len(self.seen[state]) >= self.max_repeats:
            return (
                f"Loop detected: {tool_name} called {self.max_repeats} times "
                f"with identical parameters in {self.window}s. "
                f"Stop retrying and ask the user for guidance."
            )
        return None

loop_breaker = LoopBreaker()
```

Wire it into the tool handler:

```python
from mcp.server.fastmcp.exceptions import ToolError  # fastmcp package: from fastmcp.exceptions import ToolError

def handle_tool_call(tool_name: str, params: dict):
    loop_msg = loop_breaker.check(tool_name, params)
    if loop_msg:
        raise ToolError(loop_msg)  # error result, not a returned dict

    return execute_tool(tool_name, params)
```

## Pattern 9: Return normalized inputs

```python
from datetime import datetime, timedelta
import dateparser  # pip install dateparser

def get_events(date: str):
    resolved = resolve_date(date)
    events = db.query_events(resolved)
    return {
        "events": events,
        "normalized_inputs": {
            "date": resolved.strftime("%Y-%m-%d"),
            "note": f"Interpreted '{date}' as {resolved.strftime('%Y-%m-%d')}"
        }
    }

def resolve_date(raw: str) -> datetime:
    shortcuts = {"today": datetime.now(), "yesterday": datetime.now() - timedelta(days=1)}
    return shortcuts.get(raw.lower()) or dateparser.parse(raw)
```
