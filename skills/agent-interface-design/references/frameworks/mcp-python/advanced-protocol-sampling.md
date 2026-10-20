# Python: sampling and the sampling-with-tools inner loop

> Read when: you are implementing `sampling/createMessage` or a bounded inner agent loop in a Python MCP server.

Core rules: `../../mcp/protocol-sampling.md`. Gating and fallbacks: `advanced-protocol.md`.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 2: Use Sampling to Keep the API Key on the Client Side -->
## Draft a reply on the client's model

```python
@mcp.tool()
async def draft_reply(thread_id: str, ctx: Context) -> str:
    msgs = load_thread(thread_id)
    resp = await ctx.session.create_message(
        messages=[{"role": "user", "content": {"type": "text", "text": render(msgs)}}],
        system_prompt="You draft concise professional email replies.",
        model_preferences={
            "hints": [{"name": "claude-3-5-sonnet"}],
            "intelligencePriority": 0.8,
            "speedPriority": 0.4,
        },
        max_tokens=512,
    )
    return resp.content.text
```

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 3: Sampling-With-Tools Requires Matching `ToolResultContent` For Every `ToolUseContent` -->
## Bounded inner loop with matching tool results

```python
async def inner_agent_loop(ctx: Context, goal: str, max_turns: int = 8):
    messages = [{"role": "user", "content": {"type": "text", "text": goal}}]
    tools = [{"name": "lookup", "description": "...", "inputSchema": {...}}]

    for _ in range(max_turns):
        resp = await ctx.session.create_message(
            messages=messages,
            max_tokens=1024,
            tools=tools,
            tool_choice={"type": "auto"},
        )
        messages.append({"role": "assistant", "content": resp.content})
        if resp.stop_reason == "endTurn":
            return resp.content.text
        if resp.stop_reason == "toolUse":
            for block in resp.content:
                if block.type == "tool_use":
                    result = dispatch(block.name, block.input)
                    messages.append({
                        "role": "user",
                        "content": {"type": "tool_result", "tool_use_id": block.id, "content": result},
                    })
    raise RuntimeError("Inner loop exceeded max_turns")
```
