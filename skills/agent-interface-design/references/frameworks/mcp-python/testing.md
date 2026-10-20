# Python testing: eval loop, transcript analysis, A/B prompts, execution cache

> Read when: you are implementing MCP evals, transcript-driven refactoring or the execution-state cache in Python.

Rules and rationale: `../../mcp/ops-evals.md`, `../../mcp/ops-usability-review.md`, `../../mcp/ops-execution-cache.md`. Model identifiers are in `../../fresh/mcp-testing-tools.md` and may be out of date.

<!-- src: audit-agentic-mcp/references/patterns/testing.md#1. Use Evaluation-Driven Development with Realistic Multi-Step Tasks -->
## Eval loop

```python
import anthropic

def run_eval(task: dict, tools: list) -> dict:
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": task["prompt"]}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system="You are testing MCP tools. Think step by step before each tool call.",
            tools=tools,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            return {
                "success": verify_against_ground_truth(response, task["expected"]),
                "tool_calls": count_tool_calls(messages),
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                "transcript": messages
            }

        # Process tool calls and continue the loop
        # one assistant turn, then one user turn that answers every tool_use block in it
        messages.append({"role": "assistant", "content": response.content})
        results = [{"type": "tool_result", "tool_use_id": block.id,
                    "content": execute_mcp_tool(block.name, block.input)}
                   for block in response.content if block.type == "tool_use"]
        messages.append({"role": "user", "content": results})
```

<!-- src: audit-agentic-mcp/references/patterns/testing.md#3. Feed Evaluation Transcripts Back for Auto-Refactoring -->
## Transcript analysis

```python
# 1. Run eval and capture transcripts
eval_results = []
for task in eval_tasks:
    result = run_eval(task, tools)
    eval_results.append({
        "task": task["description"],
        "success": result["success"],
        "transcript": result["transcript"],
        "tool_calls": result["tool_calls"],
        "tokens": result["tokens_used"]
    })

# 2. Feed transcripts to Claude for analysis
analysis_prompt = f"""
Analyze these MCP tool evaluation transcripts and suggest improvements:

{json.dumps(eval_results, indent=2)}

For each failure or inefficiency, identify:
1. Which tool description was ambiguous
2. What parameter naming caused confusion
3. Where the response format led the model astray
4. Specific text changes to fix each issue

Output as a structured list of changes to make.
"""
```

<!-- src: audit-agentic-mcp/references/patterns/testing.md#4. Ask the LLM to Evaluate Your Server's Usability -->
## A/B test descriptions in context

```python
# Present two description variants and ask the model to pick
prompt = """
Version A: "Searches the database for matching records."
Version B: "Find records matching your criteria. Returns up to 50 results
sorted by relevance. Use filters to narrow: status, date_range, owner."

Which description would help you use this tool more effectively? Why?
"""
```

<!-- src: audit-agentic-mcp/references/patterns/testing.md#6. Use File Hashing to Prevent Agent Reprocessing Loops -->
## Server-side execution cache

```python
import hashlib, time, json

execution_cache: dict[str, dict] = {}
CACHE_TTL = 60  # seconds

def get_cache_key(tool_name: str, params: dict) -> str:
    """Hash tool name + all params including file refs."""
    state = json.dumps({"tool": tool_name, "params": params}, sort_keys=True)
    return hashlib.sha256(state.encode()).hexdigest()

def call_tool_with_cache(tool_name: str, params: dict) -> dict:
    force = params.pop("force_refresh", False)
    key = get_cache_key(tool_name, params)
    if not force and key in execution_cache:
        entry = execution_cache[key]
        age = time.time() - entry["timestamp"]
        if age < CACHE_TTL:
            return {"result": entry["result"], "cached": True,
                    "note": f"Cached {int(age)}s ago. Use force_refresh=true to bypass."}
    result = execute_tool(tool_name, params)
    execution_cache[key] = {"result": result, "timestamp": time.time()}
    return {"result": result, "cached": False}
```
