# MCP client-quirk workaround snippets (Python, JavaScript)

> Read when: you implement a workaround from the client-compatibility patterns and need the code shape; the rules and clients affected are in `fresh/client-compatibility-*.md`.

Python snippets use FastMCP-style decorators and are illustrative.

## Pattern 1: expose a templated resource as a tool

```python
# DON'T: silently ignored by Claude Desktop
@mcp.resource("greeting://{name}")
def greet(name: str) -> str: ...

# DO: works everywhere
@mcp.tool(description="Generate a greeting for a named recipient.")
def greet(name: str) -> str: ...
```

## Pattern 3: single-argument prompt for Zed

```python
# DON'T: invisible in Zed
@mcp.prompt("code_review")
def review(path: str, language: str, strict: bool): ...

# DO: single JSON arg passes Zed's filter
@mcp.prompt("code_review")
def review(payload: str): ...  # payload: {"path": "...", "language": "...", "strict": true}
```

## Pattern 4: dual-encode every response

```python
return {
  "content": [
    {"type": "text", "text": summary_for_humans},
  ],
  "structuredContent": machine_readable_payload,
}
```

## Pattern 5: `whoami` tool for header debugging

```python
@mcp.tool(description="Echo the auth principal the server sees. Use to debug missing credentials.")
def whoami(ctx) -> dict:
    return {"authenticated_as": ctx.principal, "headers_seen": list(ctx.request.headers.keys())}
```

## Pattern 6: capability-check sampling

```python
if "sampling" in ctx.client_capabilities:
    summary = await ctx.session.create_message(prompt, max_tokens=500)
else:
    summary = local_template_summarize(data)  # no model needed
```

## Pattern 7: installer root key

```js
const key = client === "zed" ? "context_servers" : "mcpServers";
const cfg = readJson(configPath) ?? {};  // merge, never overwrite other servers
cfg[key] = { ...cfg[key], myserver: spec };
writeJson(configPath, cfg);
```

## Pattern 13: elicitation with text fallback

```python
if "elicitation" in ctx.client_capabilities:
    answer = await ctx.session.elicit(schema=ConfirmDelete)
    # proceed only when the user accepted; on decline or cancel, do nothing
else:
    return {"content": [{"type": "text",
        "text": "This action is destructive. Reply with `confirm=true` in the next call to proceed."}]}
```

## Pattern 14: MCP Apps with a text path

```python
return {
  "content": [
    {"type": "text", "text": text_summary},
    {"type": "mcp/app", "url": "https://...", "sandbox": "strict"},  # ignored elsewhere
  ],
  "structuredContent": data,
}
```

## Pattern 15: annotations for a pure read

```python
@mcp.tool(
  description="Search the knowledge base.",
  annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
)
def search(query: str) -> list: ...
```
