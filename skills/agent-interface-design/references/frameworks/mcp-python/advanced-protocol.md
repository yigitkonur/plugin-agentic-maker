# Python: capability gating, stateless check, progress, cancellation, _meta, composition

> Read when: you are implementing capability fallbacks, progress, cancellation, `_meta` propagation or a combined long-running tool in a Python MCP server (FastMCP style).

Core rules: `../../mcp/protocol-capability-gating.md`, `../../mcp/protocol-progress-and-cancellation.md`, `../../mcp/protocol-meta-keys.md`, `../../mcp/protocol-feature-composition.md`. Sampling, elicitation, roots and completion code are in the sibling files advanced-protocol-sampling, advanced-protocol-elicitation and advanced-protocol-roots-and-completion.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 1: Capability-Gate Every Advanced Feature Before Using It -->
## Capability gate with fallback

```python
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("server")

@mcp.tool()
async def summarize(doc: str, ctx: Context) -> str:
    caps = ctx.session.client_capabilities
    if caps and caps.sampling is not None:
        resp = await ctx.session.create_message(
            messages=[{"role": "user", "content": {"type": "text", "text": f"Summarize: {doc}"}}],
            max_tokens=256,
        )
        return resp.content.text
    # Fallback: ask the orchestrating agent to do it in its own context
    return (
        "SAMPLING_UNAVAILABLE: This client does not support sampling. "
        "Please summarize the following document yourself and call `save_summary` with the result.\n\n"
        + doc
    )
```

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 12: Detect Stateless HTTP Mode Early — Advanced Features Silently Break Without A Session -->
## Stateless HTTP detection

```python
mcp = FastMCP("server", stateless_http=False)  # default

@mcp.tool()
async def summarize(doc: str, ctx: Context) -> str:
    if ctx.session is None or getattr(ctx.session, "stateless", False):
        return (
            "ERROR: This server is running in stateless HTTP mode and cannot use sampling. "
            "Deploy with stateless_http=False (Streamable HTTP with sessions) to enable."
        )
    ...
```

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 8: Progress Tokens Belong In `params._meta`, Not `params` -->
## Progress reporting

```python
# Request sent by the client (illustrative)
# {"method":"tools/call",
#  "params":{"_meta":{"progressToken":"abc123"},
#            "name":"long_task","arguments":{}}}

@mcp.tool()
async def long_task(ctx: Context) -> str:
    total = 100
    for i in range(total):
        await do_chunk(i)
        # FastMCP auto-reads progressToken from _meta
        await ctx.report_progress(progress=i + 1, total=total, message=f"Processed {i + 1}/{total}")
    return "done"
```

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 9: Handle `notifications/cancelled` Cooperatively — And Never Cancel `initialize` Or Tasks -->
## Cooperative cancellation

```python
import asyncio

@mcp.tool()
async def long_search(query: str, ctx: Context) -> list[dict]:
    results = []
    for chunk in paginate(query):
        # Cooperative checkpoint — raises if cancelled
        if ctx.is_cancelled():
            raise asyncio.CancelledError("client cancelled")
        results.extend(await fetch_chunk(chunk))
    return results
```

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 10: Namespace Custom `_meta` Keys With Reverse-DNS; Reserve Un-Namespaced For The Protocol -->
## Trace ID propagation through _meta

```python
# Propagating a trace ID end-to-end
@mcp.tool()
async def process(order_id: str, ctx: Context) -> dict:
    trace_id = ctx.request_meta.get("com.acme/trace-id") or new_trace_id()
    log.info("processing", trace=trace_id, order=order_id)
    result = await backend.process(order_id, trace=trace_id)
    # Return meta on the result; clients MAY relay it
    ctx.response_meta["com.acme/trace-id"] = trace_id
    ctx.response_meta["com.acme/backend-version"] = backend.version
    return result
```

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 11: Compose Progress + Cancellation, Sampling + Elicitation, And URL-Mode + `_meta` For Full Agentic UX -->
## Elicit, long-run, then sample

```python
@mcp.tool()
async def research(topic: str, ctx: Context) -> str:
    # 1. Clarify with elicitation
    prefs = await ctx.elicit(
        message=f"How should I research '{topic}'?",
        schema=ResearchPreferences,
    )
    if prefs.action != "accept":
        return "cancelled"

    # 2. Long-running work with progress + cancellation
    sources = []
    for i, src in enumerate(iter_sources(prefs.data)):
        if ctx.is_cancelled():
            raise asyncio.CancelledError()
        await ctx.report_progress(i + 1, len(prefs.data.sources), f"Fetched {src.name}")
        sources.append(await fetch(src))

    # 3. Synthesize via sampling (client's LLM, no API key)
    resp = await ctx.session.create_message(
        messages=[{"role": "user", "content": {"type": "text", "text": synthesize_prompt(sources)}}],
        max_tokens=2048,
    )
    return resp.content.text
```
