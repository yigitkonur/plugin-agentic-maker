# Python MCP tool response examples

> Read when: you are writing Python tool handlers that return concise/detailed output, truncation guidance or next-step hints.

Explanation and rules: ../../mcp/responses-curated-and-semantic.md and ../../mcp/responses-steering-and-examples.md

## Pattern 2: response_format enum

```python
from enum import Enum

class ResponseFormat(Enum):
    DETAILED = "detailed"
    CONCISE = "concise"

@tool
def get_customer(customer_id: str, response_format: ResponseFormat = ResponseFormat.CONCISE):
    data = fetch_customer(customer_id)

    if response_format == ResponseFormat.DETAILED:
        return {
            "name": data.name,
            "email": data.email,
            "recent_transactions": data.transactions,
            "notes": data.notes,
            "internal_id": data.id,
            "thread_ts": data.thread_ts  # for downstream tool calls
        }
    else:
        return {
            "name": data.name,
            "email": data.email,
            "summary": data.summary
        }
```

## Pattern 4: Truncation guidance before the data

```python
@tool
def search_logs(query: str, limit: int = 50) -> dict:
    results = log_store.search(query, limit=limit + 1)
    truncated = len(results) > limit
    results = results[:limit]

    response = {
        "results": results,
        "count": len(results),
        "total_available": log_store.count(query),
    }

    if truncated:
        response["guidance"] = (
            f"Showing {limit} of {response['total_available']} results. "
            f"Consider filtering by date range (e.g., start_date='2025-01-01') "
            f"or adding more specific terms to narrow results."
        )

    return response
```

## Pattern 5: Next-step hints in a successful response

```python
@tool
def create_project(name: str, repo_url: str) -> dict:
    project = api.create_project(name=name, repo=repo_url)
    return {
        "status": "success",
        "project_id": project.id,
        "project_name": name,
        "message": f"Project '{name}' created successfully.",
        "next_steps": [
            f"Use add_environment_variables(project_id='{project.id}') to configure env vars.",
            f"Use create_deployment(project_id='{project.id}', branch='main') to deploy.",
            f"Use add_custom_domain(project_id='{project.id}', domain='...') to set up a domain."
        ]
    }
```
