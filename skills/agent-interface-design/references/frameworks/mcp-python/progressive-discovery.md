# Python MCP progressive discovery examples

> Read when: you are writing Python meta-tools, semantic tool search, staged discovery or session-based tool unlocking for a large tool catalog.

Explanation and rules: ../../mcp/patterns-progressive-discovery.md and ../../mcp/patterns-dynamic-tool-lists.md. FastMCP visibility transforms: progressive-discovery-fastmcp.md

## Pattern 1: list / describe / execute meta-tools

```python
# mcp = FastMCP(...); tool_registry is your catalog
@mcp.tool()
def list_tools(prefix: str = "/") -> list[str]:
    """List available tool categories or tools matching a prefix.
    Example: list_tools('/hubspot/deals/') returns deal-related tools."""
    return tool_registry.list(prefix)

@mcp.tool()
def describe_tools(tool_id: str) -> dict:
    """Get the full input schema for a specific tool.
    Call this before execute_tool to understand required parameters."""
    return tool_registry.get_schema(tool_id)

@mcp.tool()
def execute_tool(tool_id: str, arguments: dict) -> dict:
    """Execute a tool by ID with the given arguments.
    Call describe_tools first to get the correct schema."""
    return tool_registry.execute(tool_id, arguments)
```

## Pattern 2: Semantic tool search

```python
from sentence_transformers import SentenceTransformer
import faiss

class SemanticToolRouter:
    def __init__(self, tools):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.tools = tools
        texts = [f"{t.name}: {t.description}" for t in tools]
        embeddings = self.model.encode(texts)
        self.index = faiss.IndexFlatIP(embeddings.shape[1])
        self.index.add(embeddings)

    def search(self, query: str, top_k: int = 3) -> list:
        emb = self.model.encode([query])
        scores, idx = self.index.search(emb, top_k)
        return [self.tools[i] for i in idx[0] if i != -1]  # faiss pads with -1 when top_k > index size

# router = SemanticToolRouter(all_tools), built once at startup
@mcp.tool()
def find_tools(query: str) -> list[dict]:
    """Find tools matching a natural language intent.
    Example: find_tools('list recent HubSpot deals')"""
    matches = router.search(query, top_k=5)
    return [{"id": t.id, "name": t.name, "description": t.description} for t in matches]
```

## Pattern 4: Staged discovery handler

```python
def handle_discovery(stage, **kwargs):
    if stage not in ("categories", "actions", "schema"):
        return {"options": ["categories", "actions", "schema"]}  # list valid stages, no "not found"
    if stage == "categories":
        return {"stage": "categories", "options": list_available_services()}

    elif stage == "actions":
        service = kwargs["service"]
        return {"stage": "actions", "service": service,
                "options": list_actions(service)}

    elif stage == "schema":
        return {"stage": "schema",
                "schema": get_action_schema(kwargs["service"], kwargs["action"])}
```
