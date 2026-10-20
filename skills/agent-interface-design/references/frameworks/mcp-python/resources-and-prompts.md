# Python: resources, templates, prompts and the hybrid pattern

> Read when: you are implementing docs-as-resource, a prompt, or the resource-plus-search-tool hybrid in a Python MCP server (FastMCP style).

Core guidance: `../../mcp/protocol-resources.md`, `../../mcp/protocol-prompts.md`, `../../mcp/protocol-resources-vs-tools.md`.

<!-- src: audit-agentic-mcp/references/patterns/resources-and-prompts.md#1. Use Resources as On-Demand Documentation Referenced in Errors -->
## Documentation resource cited in the error

```python
@mcp.resource("docs://tools")
def get_tool_docs() -> str:
    """Complete documentation for all tools, including examples and edge cases."""
    return Path("tool_documentation.md").read_text()

@mcp.tool(description="Search for contacts. See docs://tools for detailed usage.")
def search_contacts(query: str) -> dict:
    if not query.strip():
        return {
            "content": [{
                "type": "text",
                "text": "Query cannot be empty. See docs://tools for usage examples and valid query formats."
            }],
            "isError": True
        }
    # ...
```

<!-- src: audit-agentic-mcp/references/patterns/resources-and-prompts.md#3. Use MCP Prompts for Repeatable Workflow Entry Points -->
## Prompt with an embedded resource

```python
@mcp.prompt
def analyze_bug(
    error_message: str,
    file_path: str,
    severity: str = "medium"
) -> list[dict]:
    """Structured bug analysis workflow with access to the relevant source file."""
    return [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": (
                    f"Analyze this bug systematically:\n"
                    f"Error: {error_message}\n"
                    f"File: {file_path}\n"
                    f"Severity: {severity}\n\n"
                    f"1. Identify the root cause\n"
                    f"2. Check for related issues in nearby code\n"
                    f"3. Propose a fix with test cases\n"
                    f"4. Assess risk of the fix"
                )
            }
        },
        {
            "role": "user",
            "content": {
                "type": "resource",
                "resource": {
                    "uri": f"file://{file_path}",
                    "mimeType": "text/plain"
                }
            }
        }
    ]
```

<!-- src: audit-agentic-mcp/references/patterns/resources-and-prompts.md#4. When to Use Resources vs Tools -->
## Hybrid: resource for ID access, tool for search

```python
# Resource: simple access by ID
@mcp.resource("customers://{customer_id}")
def get_customer(customer_id: str): ...

# Tool: complex search with filters
@mcp.tool
def search_customers(query: str, status: str = "active", limit: int = 10): ...
```
