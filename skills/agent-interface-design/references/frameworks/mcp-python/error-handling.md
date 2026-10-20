# Python MCP error-handling examples

> Read when: you are writing Python tool handlers that return teaching errors, prerequisite errors, retry limits or "options only" lookups.

Explanation and rules: ../../mcp/errors-protocol-vs-tool.md and ../../mcp/errors-framing-and-recovery.md. Loop detection and normalized inputs: error-handling-recovery.md

## Pattern 2: Error template

```python
def format_error(field: str, problem: str, expected: str, recovery_tool: str = None) -> dict:
    msg = f"Parameter '{field}': {problem}. Expected: {expected}."
    if recovery_tool:
        msg += f" Use {recovery_tool} to get valid values."
    return {"content": [{"type": "text", "text": msg}], "isError": True}

# Example usage:
format_error(
    field="start_date",
    problem="Date '2024-07-31' is in the past",
    expected="A future date in YYYY-MM-DD format",
    recovery_tool=None
)
# Output: "Parameter 'start_date': Date '2024-07-31' is in the past. Expected: A future date in YYYY-MM-DD format."
```

## Pattern 3: State-change prerequisite error

```python
@tool
def terminate_instance(instance_id: str):
    instance = get_instance(instance_id)
    if instance.state == "running":
        return {
            "content": [{
                "type": "text",
                "text": (
                    f"Instance '{instance_id}' is currently running. "
                    f"Call stop_instance(instance_id='{instance_id}') first, "
                    f"wait for it to reach 'stopped' state, then retry "
                    f"terminate_instance(instance_id='{instance_id}')."
                )
            }],
            "isError": True
        }
    # ... proceed with termination
```

## Pattern 4: Retry limit and fallback

```python
@tool
def process_payment(order_id: str, _retry_count: int = 0):
    try:
        return payment_api.charge(order_id)
    except TransientError:
        if _retry_count >= 2:
            return {
                "content": [{
                    "type": "text",
                    "text": (
                        f"Payment processing failed after 3 attempts for order '{order_id}'. "
                        f"Ask the user to complete payment manually at: "
                        f"https://dashboard.example.com/orders/{order_id}/pay"
                    )
                }],
                "isError": True
            }
        return {
            "content": [{
                "type": "text",
                "text": (
                    f"Payment processing temporarily failed (attempt {_retry_count + 1}/3). "
                    f"Call process_payment(order_id='{order_id}', _retry_count={_retry_count + 1}) to retry."
                )
            }],
            "isError": True
        }
```

## Pattern 5: Brief description, errors carry the long tail

```python
@tool(description="Search for contacts by name, email, or company.")
def search_contacts(query: str, limit: int = 10):
    """
    Description is intentionally brief. Edge cases are handled by errors.
    """
    if not query.strip():
        return error("Query cannot be empty. Provide a name, email, or company name.")

    if limit > 100:
        return error(
            f"Limit {limit} exceeds maximum of 100. "
            f"Call search_contacts(query='{query}', limit=100) instead."
        )

    results = db.search(query, limit=limit)
    if not results:
        return {
            "content": [{"type": "text", "text":
                f"No contacts found for '{query}'. "
                f"Try a broader search term or check spelling. "
                f"You can also use list_companies() to browse available companies."
            }],
            "isError": False  # Not an error - valid empty result with guidance
        }
    return format_results(results)
```

## Pattern 6: Preventive framing

```python
def schedule_meeting(date: str, title: str):
    parsed = parse_date(date)
    if parsed < datetime.now():
        return {
            "content": [{"type": "text", "text":
                f"Great catch — {date} is in the past. "
                f"Use a future date (after {datetime.now().strftime('%Y-%m-%d')}) "
                f"and retry: schedule_meeting(date='<future_date>', title='{title}')"
            }],
            "isError": True
        }
    # proceed with scheduling...
```

## Pattern 7: Options only, no "not found"

```python
MODULES = {"fs", "http", "path", "crypto", "stream"}

def load_module(name: str):
    if name not in MODULES:
        available = ", ".join(sorted(MODULES))
        # Don't say "not found" — just show what's there
        return {
            "content": [{"type": "text", "text":
                f"Available modules: {available}. "
                f"Retry load_module(name='<module>') with one of these."
            }],
            "isError": True
        }
    return {"content": [{"type": "text", "text": f"Loaded {name} successfully."}]}
```
