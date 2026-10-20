# Python MCP steering helpers

> Read when: you are writing Python helpers that wrap tool output in instruction/data tags or validate the next tool against a server-side graph.

Explanation, the steering-versus-injection tension and the `allowed_next_tools` rule: ../../decisions/steering-contract.md

## Separate instructions from data

```python
def format_tool_response(data: dict, instructions: str, next_action: str = None) -> str:
    parts = [f"<instructions>\n{instructions}\n</instructions>",
             f"<data>\n{json.dumps(data, indent=2)}\n</data>"]
    if next_action:
        parts.append(f"<next_action>{next_action}</next_action>")
    return "\n".join(parts)
```

## Server-side tool graph against workflow hijacking

```python
TOOL_GRAPH = {
    "search":   {"allowed_next": ["validate", "search_broader"]},
    "validate": {"allowed_next": ["summarize", "search"]},
    "summarize": {"allowed_next": ["export", "refine"]},
}

def validate_next_tool(current_tool: str, requested_next: str) -> bool:
    allowed = TOOL_GRAPH.get(current_tool, {}).get("allowed_next", [])
    if requested_next not in allowed:
        raise ValueError(f"'{current_tool}' cannot invoke '{requested_next}'. Allowed: {allowed}")
    return True
```
