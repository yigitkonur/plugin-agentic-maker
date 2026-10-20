# Python MCP error-handling examples

> Read when: you are writing Python tool handlers that return teaching errors, prerequisite errors, retry limits or "options only" lookups.

Explanation and rules: ../../mcp/errors-protocol-vs-tool.md and ../../mcp/errors-framing-and-recovery.md. Loop detection and normalized inputs: error-handling-recovery.md

## Pattern 2: Error template

```python
from typing import NoReturn
from mcp.server.fastmcp.exceptions import ToolError  # fastmcp package: from fastmcp.exceptions import ToolError

def format_error(field: str, problem: str, expected: str, recovery_tool: str | None = None) -> NoReturn:
    msg = f"Parameter '{field}': {problem}. Expected: {expected}."
    if recovery_tool:
        msg += f" Use {recovery_tool} to get valid values."
    raise ToolError(msg)  # FastMCP turns this into an error result (isError: true)

# Example usage inside a tool:
format_error(
    field="start_date",
    problem="Date '2024-07-31' is in the past",
    expected="A future date in YYYY-MM-DD format",
    recovery_tool=None
)
# Error text: "Parameter 'start_date': Date '2024-07-31' is in the past. Expected: A future date in YYYY-MM-DD format."
```

A bare returned dict with an `isError` key is ordinary tool data, not the protocol error flag; raise `ToolError` in every pattern below.

## Pattern 3: State-change prerequisite error

```python
@mcp.tool()  # mcp = FastMCP(...)
def terminate_instance(instance_id: str):
    instance = get_instance(instance_id)
    if instance.state == "running":
        raise ToolError(
            f"Instance '{instance_id}' is currently running. "
            f"Call stop_instance(instance_id='{instance_id}') first, "
            f"wait for it to reach 'stopped' state, then retry "
            f"terminate_instance(instance_id='{instance_id}')."
        )
    # ... proceed with termination
```

## Pattern 4: Retry limit and fallback

```python
@mcp.tool()
def process_payment(order_id: str, _retry_count: int = 0):
    try:
        return payment_api.charge(order_id)
    except TransientError:
        if _retry_count >= 2:
            raise ToolError(
                f"Payment processing failed after 3 attempts for order '{order_id}'. "
                f"Ask the user to complete payment manually at: "
                f"https://dashboard.example.com/orders/{order_id}/pay"
            )
        raise ToolError(
            f"Payment processing temporarily failed (attempt {_retry_count + 1}/3). "
            f"Call process_payment(order_id='{order_id}', _retry_count={_retry_count + 1}) to retry."
        )
```

## Pattern 5: Brief description, errors carry the long tail

```python
@mcp.tool(description="Search for contacts by name, email, or company.")
def search_contacts(query: str, limit: int = 10):
    """
    Description is intentionally brief. Edge cases are handled by errors.
    """
    if not query.strip():
        raise ToolError("Query cannot be empty. Provide a name, email, or company name.")

    if limit > 100:
        raise ToolError(
            f"Limit {limit} exceeds maximum of 100. "
            f"Call search_contacts(query='{query}', limit=100) instead."
        )

    results = db.search(query, limit=limit)
    if not results:
        # Not an error: a valid empty result with guidance, returned normally
        return (
            f"No contacts found for '{query}'. "
            f"Try a broader search term or check spelling. "
            f"You can also use list_companies() to browse available companies."
        )
    return results
```

## Pattern 6: Preventive framing

```python
from datetime import datetime

def schedule_meeting(date: str, title: str):
    parsed = parse_date(date)
    if parsed < datetime.now():
        raise ToolError(
            f"Great catch — {date} is in the past. "
            f"Use a future date (after {datetime.now().strftime('%Y-%m-%d')}) "
            f"and retry: schedule_meeting(date='<future_date>', title='{title}')"
        )
    # proceed with scheduling...
```

## Pattern 7: Options only, no "not found"

```python
MODULES = {"fs", "http", "path", "crypto", "stream"}

def load_module(name: str):
    if name not in MODULES:
        available = ", ".join(sorted(MODULES))
        # Don't say "not found" — just show what's there
        raise ToolError(
            f"Available modules: {available}. "
            f"Retry load_module(name='<module>') with one of these."
        )
    return f"Loaded {name} successfully."
```
