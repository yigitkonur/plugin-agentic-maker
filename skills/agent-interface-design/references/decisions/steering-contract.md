# Steering contract: guiding the agent through tool output without opening an injection channel

> Read when: a tool response or error will tell the agent what to do next, or you are auditing whether tool output is trusted too much or steers too little.

<!-- src: audit-agentic-mcp/references/patterns/prompt-gates.md#Prompt Gates -->
Tool responses go straight into the agent's context and steer it mid-conversation; use that deliberately. Other files link here for the tension. Code: `../frameworks/mcp-python/prompt-gates.md`, `../frameworks/mcp-ts/prompt-gates.md`, `../frameworks/mcp-ts/agentic-patterns.md`.

## The tension and the bridge

| Position | Claim | Consequence |
|---|---|---|
| Steering | Steering text in tool output is the strongest lever for in-flight guidance. | Design every response as guidance, not just data. |
| Injection | The same channel is the attack surface: tool output is untrusted input. | A poisoned or compromised tool can redirect the agent. |

> Reconciled: the sources treat steering text in tool output as the strongest lever and the same channel as an attack surface; this file keeps both with the bridge below.

Bridge: put all steering in one namespaced block (`_agent_guidance` with a `source`) plus an `allowed_next_tools` list that the server validates against its own tool graph. Keep the block to text your own server authored; external content stays in the data part.

<!-- src: audit-agentic-mcp/references/patterns/prompt-gates.md#1. Tool Responses Have Surprisingly High Authority -->
## Tool responses carry high authority

Authority depends on the model: some use a dedicated `tool` role that may rank above user messages, others treat the result as fresh, recency-weighted context (per-model table: `../fresh/mcp-model-behavior.md`). Either way a response beats the system prompt for in-flight guidance: it arrives via a trusted channel, sits right before the next generation, and models treat tool output as ground truth.

`{"results": [...], "_instructions": "Present these results as a numbered list. Flag any items older than 2023 as potentially outdated."}` is followed with high compliance, which is also why the bridge above is required.

<!-- src: audit-agentic-mcp/references/patterns/prompt-gates.md#2. Use XML Tags to Separate Instructions from Data -->
## Separate instructions from data

Models separate behavioral instructions from raw data only when they are structurally separated; inline instructions lower compliance.

```xml
<instructions>
Analyze these results step-by-step.
If fewer than 3 relevant results, call search_broader tool.
Do not present results the user didn't ask for.
</instructions>
<data>
{"results": [{"title": "MCP Protocol Spec", "relevance": 0.95}, {"title": "JSON-RPC Overview", "relevance": 0.72}]}
</data>
<next_action>Call validate_relevance with top 3 results</next_action>
```

`<instructions>` is what to do, `<data>` what to work with, `<next_action>` where to go. Anti-pattern: `{"results": [...], "note": "Remember to validate these before showing them, and also call the verify tool next"}`; the model treats `note` as data, not a directive. The data block is the only place external content may appear.

<!-- src: audit-agentic-mcp/references/patterns/prompt-gates.md#3. Build State Machines via Sequential Tool Responses -->
## Build state machines from sequential responses

Each response sets up the next step, making the server a lightweight state machine ("flattening the agent back into the model"):

```
Tool 1 (plan) response:     <state>planning</state>
  <instructions>Prioritize 2024+ sources. Max 5 queries.</instructions>   <next_tool>search</next_tool>
Tool 2 (search) response:   <state>searching</state>
  <instructions>Cross-check facts across 2+ sources. Drop confidence < 0.6.</instructions>   <next_tool>validate</next_tool>
Tool 3 (validate) response: <state>complete</state>
  <instructions>Present with confidence scores. Cite sources inline.</instructions>
```

Each response is a prompt gate: (1) declares the current state, (2) injects step-specific instructions, (3) points to the next tool so the model does not wander. Gates guide; to block out-of-order calls use server stages (`../mcp/patterns-guarded-workflows.md`).

<!-- src: audit-agentic-mcp/references/patterns/prompt-gates.md#4. Namespace Injected Instructions to Prevent Conflicts -->
## Namespace guidance and list allowed next tools

When several tools inject instructions they can contradict each other, and an unnamed block invites workflow hijacking. Use one consistent shape in every response:

```json
{
  "result": {"data": "..."},
  "_agent_guidance": {
    "source": "search_tool",
    "instructions": "Cross-reference these results before presenting to the user.",
    "next_action": {"tool": "validate", "required": true},
    "allowed_next_tools": ["validate", "summarize", "export"]
  }
}
```

1. **Attribution:** `source` tells the model and debuggers which tool issued the instruction.
2. **Conflict resolution:** when two tools disagree, the model can weigh by source.
3. **Security:** `allowed_next_tools` stops a compromised tool from redirecting the agent.

Enforce with a server-side tool graph: map each tool to its `allowed_next` list (for example `search` -> `validate`, `search_broader`; `validate` -> `summarize`, `search`; `summarize` -> `export`, `refine`) and reject a requested next tool that is not listed with "'{current}' cannot invoke '{requested}'. Allowed: [...]". Status: `_agent_guidance` and graph validation are proposed patterns, not established standards.

<!-- src: audit-agentic-mcp/references/patterns/prompt-gates.md#5. Recommend the Next Tool or Query Frontier Explicitly -->
## Recommend the next tool or query frontier

Recommending the next tool is often the correct design, especially for research, search and investigation tools where the agent would otherwise waste turns on the obvious follow-up. The rule: **recommend aggressively, execute conservatively.**

Shape (inside `_agent_guidance`): `source`, `mode: "advisory"`, `next_action` (`tool`, `reason`), `recommended_queries` (each with `query`, `reason`, `confidence`, for example 0.83 and 0.78), `stop_conditions` ("Stop expanding when two consecutive waves add fewer than 2 novel authoritative domains.", "Stop after 12 total searches."), `server_actions_taken` (for example an `internal_planner_turn` with its purpose).

Why: each call becomes a planner checkpoint and the model focuses on evidence gaps. Better than "here are 10 links, good luck": return the results, the missing angles, the best next queries and the stop conditions.

Guardrails:
- `mode: advisory` means the server is steering, not silently taking external actions.
- Say in `server_actions_taken` if the server spent an internal planning turn.
- If the next action is mandatory for safety, mark it required and validate it against the server-side graph.
- Keep recommendations ranked; five good options beat twenty mediocre ones.

The response is the answer plus the best available continuation. Bounded internal planning: `../mcp/patterns-bounded-continuation.md`.

<!-- src: audit-agentic-mcp/references/patterns/agentic-patterns.md#2. HATEOAS: State-Based Available Actions -->
## State-based available actions (HATEOAS)

Include a dynamic `_available_actions` field in every tool response, computed from the current resource state, so the agent learns what it can do next from the response rather than from documentation. Instead of hyperlinks, return structured action descriptors: `tool`, `description`, `required_params`.

By deployment status:
- `running`: `get_metrics`, `rollback_deployment`, `scale_deployment` (params `deployment_id`, `replicas`).
- `failed`: `get_logs`, `rollback_deployment` ("Restore last known good version").
- `stopped`: `start_deployment`.
- otherwise: none.

Benefits over static docs: actions are always accurate for the current state; no invalid transition is attempted (scaling a stopped deployment); no "what can I do?" tool is needed. These descriptors are guidance too: namespace them under `_agent_guidance`, consistent with `allowed_next_tools`.
