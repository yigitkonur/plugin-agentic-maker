# Python MCP planner, sandbox and CRUD examples

> Read when: you are writing a Python MCP server and need the planner tool, code-execution sandbox, consolidated-call, combined-CRUD and toolhost examples.

Explanation and rules: ../../mcp/design-workflow-planner-and-facade.md

## Pattern 4: Planner tool

```python
@mcp.tool(description="Get the recommended workflow plan for the current task. Call this FIRST before using any other visualization tools.")
def create_plan(task_description: str) -> dict:
    return {
        "workflow": [
            {"step": 1, "tool": "load_data", "description": "Load the dataset", "required_params": ["file_path"]},
            {"step": 2, "tool": "analyze_columns", "description": "Understand data types and distributions"},
            {"step": 3, "tool": "create_chart", "description": "Generate the visualization", "required_params": ["chart_type", "x_column", "y_column"]},
            {"step": 4, "tool": "export_dashboard", "description": "Export the final result"}
        ],
        "instructions": "Follow these steps in order. Each tool's response will provide specific guidance for the next step.",
        "important": "Do not skip steps. Step 2 output is required for step 3."
    }
```

## Pattern 5: Code-execution sandbox

Tool definition:

```json
{
  "name": "execute_code",
  "description": "Run Python code in a secure sandbox with access to pre-authenticated API clients (salesforce_client, s3_client). Use for batch operations, data processing, or any task requiring loops/parallelism.",
  "input_schema": {
    "type": "object",
    "properties": {
      "code": {"type": "string", "description": "Python code to execute."},
      "timeout": {"type": "integer", "default": 300, "description": "Execution timeout in seconds."}
    },
    "required": ["code"]
  }
}
```

Example LLM-generated code:

```python
from concurrent.futures import ThreadPoolExecutor
import json

def fetch_page(p):
    return salesforce_client.fetch_leads(page=p, limit=1000)

first = fetch_page(1)
total_pages = (first['total_count'] + 999) // 1000

all_leads = []
with ThreadPoolExecutor(max_workers=10) as exe:
    for f in exe.map(fetch_page, range(1, total_pages + 1)):
        all_leads.extend(f['leads'])

s3_url = s3_client.upload(
    data=json.dumps(all_leads),
    filename=f"leads_{len(all_leads)}.json"
)
return {"status": "success", "total": len(all_leads), "s3_url": s3_url}  # the sandbox runs this as a function body
```

Security requirements (non-negotiable):
- Run in isolated containers with `--no-new-privileges`
- Drop all capabilities, mount a read-only filesystem
- Enforce CPU/memory limits via cgroups
- Restrict network egress to whitelisted endpoints
- Provide API clients pre-authenticated; never expose raw keys
- Disallow `eval`/`exec` on untrusted strings
- Set hard timeout limits

## Pattern 6: 3-5 calls, not 20+

```python
# Before: 12+ calls to analyze a repo
list_repos()              # Call 1
get_repo(id)              # Call 2
list_branches(repo_id)    # Call 3
get_branch(repo_id, "main")  # Call 4
list_commits(branch_id)   # Call 5-6 (pagination)
get_commit(commit_id)     # Call 7-12 (per commit)

# After: 2 calls
@mcp.tool(description="Get recent activity summary for a repository. Returns latest commits, active branches, and contributor stats for the specified time range.")
def get_repo_activity(
    repo: str,
    days: int = 7,
    max_commits: int = 20
) -> dict:
    repo_info = api.get_repo(repo)
    branches = api.list_branches(repo)
    commits = api.list_commits(repo, since=days_ago(days), limit=max_commits)
    return {
        "repo": repo_info.name,
        "default_branch": repo_info.default_branch,
        "active_branches": [b.name for b in branches if b.updated_recently(days)],
        "recent_commits": [{"sha": c.sha[:8], "message": c.message, "author": c.author} for c in commits],
        "summary": f"{len(commits)} commits across {len(branches)} branches in the last {days} days."
    }
```

## Pattern 7: Combined CRUD tool

```python
@mcp.tool(description="Manage users. Actions: 'list' (filter by role/status), 'get' (by user_id), 'create' (name+email required), 'update' (user_id + fields to change), 'delete' (by user_id, irreversible).")
def manage_user(
    action: Literal["list", "get", "create", "update", "delete"],
    user_id: str | None = None,
    filters: dict | None = None,
    data: dict | None = None
) -> dict:
    match action:
        case "list":
            return {"users": db.users.find(filters or {})}
        case "get":
            return {"user": db.users.find_one(user_id)}
        case "create":
            return {"user": db.users.insert(data), "status": "created"}
        case "update":
            db.users.update(user_id, data)
            return {"user": db.users.find_one(user_id), "status": "updated"}
        case "delete":
            db.users.delete(user_id)
            return {"status": "deleted", "user_id": user_id}
```

## Pattern 8: Toolhost / facade

```python
from mcp.server.fastmcp.exceptions import ToolError  # fastmcp package: from fastmcp.exceptions import ToolError

OPERATIONS = {
    "list_users":    {"handler": list_users,    "args": ["filters", "page"]},
    "get_user":      {"handler": get_user,      "args": ["user_id"]},
    "create_user":   {"handler": create_user,   "args": ["name", "email", "role"]},
    "list_projects": {"handler": list_projects,  "args": ["owner_id", "status"]},
    "get_project":   {"handler": get_project,    "args": ["project_id"]},
    "export_data":   {"handler": export_data,    "args": ["entity", "format"]},
}

@mcp.tool(description=f"Admin API gateway. Operations: {', '.join(OPERATIONS.keys())}. Pass the operation name and its arguments.")
def admin_toolhost(
    operation: str,
    args: dict | None = None
) -> dict:
    args = args or {}
    if operation not in OPERATIONS:
        raise ToolError(f"Unknown operation. Available: {list(OPERATIONS.keys())}")

    op = OPERATIONS[operation]
    missing = [a for a in op["args"] if a not in args]
    if missing:
        raise ToolError(f"Missing required args for {operation}: {missing}")

    try:
        result = op["handler"](**args)
        return {"operation": operation, "status": "success", "result": result}
    except Exception as e:
        raise ToolError(f"{operation} failed: {e}") from e
```
