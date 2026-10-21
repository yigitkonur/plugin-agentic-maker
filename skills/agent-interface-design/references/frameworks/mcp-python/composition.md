# Python composition: gateway, composable servers, resources, providers

> Read when: you are implementing MCP server composition, a gateway or a one-tool-plus-resources wrapper in Python (FastMCP style).

Rules and rationale: `../../mcp/ops-composition-patterns.md` and `../../mcp/ops-gateway.md`. Product and version names: `../../fresh/mcp-gateway-tools.md`.

<!-- src: audit-agentic-mcp/references/patterns/composition.md#1. Use a Meta-Server for Cross-Cutting Concerns -->
## Gateway middleware chain

```python
from mcp.server.fastmcp.exceptions import ToolError  # fastmcp package: from fastmcp.exceptions import ToolError

class MCPGateway:
    def __init__(self):
        self.servers = {}  # name -> MCP server connection
        self.middleware = [
            GatewayAuth(),
            RateLimitMiddleware(max_requests=100, window_seconds=60),
            AuditLogMiddleware(),
        ]

    def register(self, name: str, server_config: dict):
        self.servers[name] = connect_mcp_server(server_config)

    async def handle_tool_call(self, tool_name: str, args: dict, ctx: Context):
        # Run middleware chain
        for mw in self.middleware:
            await mw.before(tool_name, args, ctx)

        # Route to correct server based on namespace
        # longest registered prefix wins, so server names may contain "_" (e.g. "my_db")
        names = [n for n in self.servers if tool_name.startswith(n + "_")]
        if not names:
            raise ToolError(f"Unknown tool '{tool_name}'. Servers: {sorted(self.servers)}")
        server = self.servers[max(names, key=len)]

        result = await server.call_tool(tool_name, args)

        for mw in reversed(self.middleware):
            result = await mw.after(tool_name, result, ctx)

        return result
```

FastMCP 3.0 approach:

```python
mcp = FastMCP("Gateway")

# Mount sub-servers with namespace transforms
mcp.mount(github_server, namespace="github")
mcp.mount(jira_server, namespace="jira")
mcp.mount(slack_server, namespace="slack")

# Apply cross-cutting middleware (FastMCP's own class, not the GatewayAuth above;
# namespace/prefix and tag/tags spellings are version-specific, check the FastMCP docs)
mcp.add_transform(AuthMiddleware(tag="all", scopes={"authenticated"}))
```

<!-- src: audit-agentic-mcp/references/patterns/composition.md#2. Design Composable Servers That the LLM Orchestrates -->
## Composable servers

```python
# Server 1: GitHub Analysis
@mcp.tool(description="Analyze a GitHub repository's structure, dependencies, and security-relevant patterns.")
def github_analyze(repo_url: str) -> dict:
    return {
        "description": "Payment processing API using Express.js with Stripe integration",
        "dependencies": [...],
        "identified_components": ["auth", "payment", "webhook_handler"],
        "_agent_guidance": {
            "source": "github_analyze",
            "instructions": "Use threat_framework() with this description for security analysis.",
            "allowed_next_tools": ["threat_framework"],
        },
    }

# Server 2: STRIDE Threat Framework
@mcp.tool(description="Get STRIDE threat analysis framework data for an application.")
def threat_framework(app_description: str) -> dict:
    return {
        "stride_categories": {...},
        "context_analysis": analyze_app_context(app_description),
        "report_template": "Generate a threat report using the above framework.",
        "data_for_report": {...}  # Raw data for LLM assembly
    }
```

The `_agent_guidance` block is steering text in tool output; see `../../decisions/steering-contract.md`.

<!-- src: audit-agentic-mcp/references/patterns/composition.md#3. Wrap Complex APIs in One Tool + Resource Documentation -->
## One tool plus resource documentation

```python
@mcp.tool(description="Execute an API operation. Use resources at tool://{client}/{method} to see available methods and parameters.")
def api_call(client: str, method: str, params: dict | None = None) -> dict:
    """Single tool wrapping the entire API surface."""
    api_client = get_client(client)
    return api_client.call(method, **(params or {}))

@mcp.resource("tool://all")
def list_all_clients() -> str:
    """List all available API clients and their methods."""
    return json.dumps({c.name: list(c.methods.keys()) for c in clients})

@mcp.resource("tool://{client}/{method}")
def get_method_docs(client: str, method: str) -> str:
    """Detailed documentation for a specific API method."""
    return get_client(client).get_method_docs(method)

@mcp.resource("tool://{client}/{method}/{parameter}")
def get_parameter_docs(client: str, method: str, parameter: str) -> str:
    """Detailed docs for a specific parameter of a method."""
    return get_client(client).get_param_docs(method, parameter)
```

<!-- src: audit-agentic-mcp/references/patterns/composition.md#4. Use the Provider + Transform Architecture for Maximum Flexibility -->
## Providers and transforms

Provider types:

```python
# Local functions
@mcp.tool()
def my_tool(): ...

# From a directory of Python files
admin_provider = FileSystemProvider("./admin_tools", reload=True)

# From an OpenAPI spec
api_provider = OpenAPIProvider("https://api.example.com/openapi.json")

# From a remote MCP server
remote_provider = MCPClientProvider("https://remote-mcp.example.com")

# From instruction files (skills)
skills_provider = SkillsProvider("./skills/")
```

Transform examples:

```python
# Namespace all tools from a provider
mcp.mount(github_provider, prefix="github")
# Tools become: github_create_pr, github_list_repos, etc.

# Filter by version
mcp.add_transform(VersionFilter(select="latest"))

# Gate with authentication
mcp.add_transform(AuthGate(tags={"admin"}, scopes={"super-user"}))

# Rename for consistency
mcp.add_transform(RenameTransform({"old_name": "new_name"}))
```
