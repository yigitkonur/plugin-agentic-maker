# Python MCP context-budget examples

> Read when: you are writing a Python MCP server and need the code-execution gateway, tiered response sizing or CLI-output cleaning.

Explanation and rules: ../../mcp/budget-tool-definitions.md and ../../mcp/budget-response-size.md

## Section 2: Code-execution gateway

```python
# Single gateway tool registered in the MCP server
@mcp.tool()  # mcp = FastMCP(...)
async def execute_code(code: str, language: str = "python") -> str:
    """
    Execute code in sandbox. Use list_servers(), list_tools(server),
    get_tool_schema(server, tool) to discover capabilities on demand.
    """
    sandbox_globals = {
        "list_servers": lambda: ["filesystem", "github", "slack"],
        "list_tools": _list_tools_brief,       # returns name + 1-line desc only
        "get_tool_schema": _get_schema_on_demand,  # full JSON schema on request
        "call_tool": _call_tool,
    }
    # ILLUSTRATION ONLY: exec() is not a sandbox. It runs in this process with Python's builtins available,
    # so model-supplied code can import modules and open files. Run it in a separate restricted process
    # or container with no network and no file access, and only pass it the four functions above.
    exec(compile(code, "<sandbox>", "exec"), sandbox_globals)
    return sandbox_globals.get("__result__", "")

async def _list_tools_brief(server: str) -> list[dict]:
    # Returns minimal shape -- no full schemas injected into context
    tools = await registry.get_tools(server)
    return [{"name": t.name, "summary": t.description[:80]} for t in tools]

async def _get_schema_on_demand(server: str, tool: str) -> dict:
    # Full schema fetched only when the model explicitly requests it
    return await registry.get_full_schema(server, tool)
```

Model usage pattern (lazy discovery):

```python
code = """
servers = list_servers()                     # → ["filesystem", "github"]
tools   = list_tools("github")               # → [{"name": "create_pr", "summary": "..."}]
schema  = get_tool_schema("github", "create_pr")  # → full JSON schema
result  = call_tool("github", "create_pr", {"title": "Fix bug", "body": "..."})
__result__ = result
"""
```

## Section 3: Tiered verbosity

```python
from dataclasses import dataclass

CONTEXT_THRESHOLDS = {"full": 0.70, "summary": 0.40}

@dataclass
class ContextBudget:
    session_tokens: int
    total_window: int

    @property
    def remaining_fraction(self) -> float:
        return max(0.0, 1.0 - self.session_tokens / self.total_window)

    @property
    def tier(self) -> str:
        r = self.remaining_fraction
        if r >= CONTEXT_THRESHOLDS["full"]:
            return "full"
        if r >= CONTEXT_THRESHOLDS["summary"]:
            return "summary"
        return "minimal"

def tiered_response(records: list[dict], budget: ContextBudget) -> dict:
    tier = budget.tier

    if tier == "full":
        return {"results": records, "total": len(records)}

    if tier == "summary":
        return {
            "total": len(records),
            "sample": records[:5],
            "detail_available": True,
            "hint": f"Showing 5 of {len(records)}. Call get_details(id) for full records.",
        }

    # minimal -- only count + directive
    return {
        "total": len(records),
        "hint": "Context low. Narrow your query or call get_details(id) for a specific record.",
    }
```

## Section 4: Strip ANSI codes and progress bars

```python
import os  # the source omitted this import; run_cli_tool needs it
import re
import subprocess

# Patterns to strip from CLI output
_ANSI_ESCAPE   = re.compile(r'\x1b\[[0-9;]*[mGKHF]')   # colors, cursor movement
_ANSI_ERASE    = re.compile(r'\x1b\[[0-9]*[JK]')         # screen/line erase
_CR_PROGRESS   = re.compile(r'[^\n]*\r')                  # carriage-return redraws
_SPINNER_CHARS = re.compile(r'[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏]')           # spinner frames
_BOX_DRAWING   = re.compile(r'[─│┌┐└┘├┤┬┴┼╭╮╯╰]')       # box-drawing unicode

def clean_cli_output(raw: str) -> str:
    s = _ANSI_ESCAPE.sub('', raw)
    s = _ANSI_ERASE.sub('', s)
    s = _CR_PROGRESS.sub('', s)
    s = _SPINNER_CHARS.sub('', s)
    s = _BOX_DRAWING.sub('', s)
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s.strip()

def run_cli_tool(cmd: list[str]) -> str:
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env={**os.environ, "NO_COLOR": "1", "TERM": "dumb"},  # suppress at source too
    )
    combined = result.stdout + ("\n" + result.stderr if result.stderr else "")
    return clean_cli_output(combined)

# Usage in an MCP tool handler
@mcp.tool()  # mcp = FastMCP(...)
async def git_log(n: int = 10) -> str:
    """Recent git log with stats."""
    return run_cli_tool(["git", "log", f"-{n}", "--stat", "--no-color"])
```
