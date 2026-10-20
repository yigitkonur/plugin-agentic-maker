# Python MCP tool design examples

> Read when: you are writing a Python MCP server and need the intent-based, smart-database and workflow-tool examples.

Explanation and rules: ../../mcp/design-intent-based-tools.md

## Pattern 1: Intent-centric tool instead of endpoint wrappers

```python
# API-centric (bad): the model loops and makes 20+ calls
#   get_members()          -> list of member IDs
#   get_member_activity()  -> activity for one member
#   get_member_posts()     -> posts for one member
#   get_member_comments()  -> comments for one member

# Intent-centric (good): one call, the server orchestrates
@tool(description="Get activity insights for all members in a space. Returns members sorted by engagement with their posts, comments, and last active date.")
def get_space_activity(space_id: str, days: int = 30, sort_by: str = "total_activity") -> dict:
    members = api.get_members(space_id)
    for m in members:
        m.activity = api.get_activity(m.id, days=days)
        m.posts = api.get_posts(m.id, days=days)
    return {
        "members": sorted(members, key=lambda m: m.activity.total, reverse=True),
        "summary": f"Found {len(members)} members active in the last {days} days.",
        "next_steps": "Use bulk_message(member_ids=[...]) to contact specific members."
    }
```

## Pattern 2: Smart database, not smart analyst

```python
# Wrong: "Smart Analyst" (brittle keyword matching, artificial limit)
def analyze_threats(description: str):
    threats = []
    if "payment" in description:  # Brittle keyword matching
        threats.append("Payment fraud")
    if "user" in description:
        threats.append("Identity spoofing")
    return {"threats": threats[:5]}  # Artificial limit for "readability"

# Right: "Smart Database" (complete framework data, the model analyses)
def get_threat_framework(app_description: str):
    return {
        "stride_categories": {
            "spoofing": {
                "description": "Identity spoofing attacks",
                "traditional_threats": ["User impersonation", "Credential theft"],
                "ai_ml_threats": ["Deepfake attacks", "Prompt injection"],
                "mitigation_patterns": ["MFA", "Certificate-based auth"],
                "indicators": ["login", "auth", "session", "token", "identity"]
            },
            # ... all categories with COMPLETE data
        },
        "context_analysis": analyze_app_context(app_description),
        "report_template": "Use the above framework data to generate a threat report."
    }
```

## Pattern 3: One workflow tool instead of four steps

```python
# Before (4 separate tools)
create_project(name, repo)       # Tool 1
add_env_vars(pid, vars)          # Tool 2
create_deployment(pid, branch)   # Tool 3
add_domain(pid, domain)          # Tool 4

# After (1 workflow tool)
@tool(description="Deploy a new project end-to-end. Creates the project, configures environment variables, deploys from the specified branch, and sets up the custom domain.")
def deploy_project(
    repo_url: str,
    domain: str,
    env_vars: dict,
    branch: str = "main"
) -> dict:
    pid = create_project(repo_url)
    add_env_vars(pid, env_vars)
    deployment = create_deployment(pid, branch)
    add_domain(pid, domain)
    return {
        "status": "success",
        "project_id": pid,
        "deployment_url": deployment.url,
        "domain": domain,
        "message": f"Project deployed to {domain} from {branch} branch."
    }
```

Implementation tip: wrap each sub-step in try/except and return a structured error naming the stage that failed, so the model knows what already completed.
