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
            "hints": [{"name": "claude"}],  # substring hint, not a pinned model id
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
            tool_choice={"mode": "auto"},  # toolChoice is {mode: auto|required|none}; the client must declare sampling.tools
        )
        messages.append({"role": "assistant", "content": resp.content})
        if resp.stop_reason == "endTurn":
            return resp.content.text
        if resp.stop_reason == "toolUse":
            # one user message holding only tool results, one per tool_use block (the spec forbids mixing in other content)
            results = [{"type": "tool_result", "toolUseId": block.id,
                        "content": [{"type": "text", "text": dispatch(block.name, block.input)}]}
                       for block in resp.content if block.type == "tool_use"]
            messages.append({"role": "user", "content": results})
    raise RuntimeError("Inner loop exceeded max_turns")
```
