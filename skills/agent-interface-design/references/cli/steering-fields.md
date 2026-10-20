# Steering Fields in CLI Output

> Read when: you are adding next-step guidance to a CLI's JSON output, or deciding whether a CLI may run a small internal planner.

Steering text in tool output is the strongest lever over an agent and the same channel is an attack surface. The rule for bridging the two is in `../decisions/steering-contract.md`; read it before shipping any `guidance` field.

<!-- src: audit-agentic-cli/references/agent-integration.md#16. Steering Contract: Put Next-Step Guidance in CLI stdout -->
## Put next-step guidance in stdout

What works for MCP tool steering also applies to a CLI called by an agent: stdout is not just a payload channel, it is the continuation contract. Return guidance in a stable top-level field so the agent can decide what to do next without guessing:

```json
{
  "ok": true,
  "result": {
    "query": "technical seo agent workflows",
    "results": ["..."]
  },
  "guidance": {
    "summary": "Current results cover general overviews but miss concrete CLI examples.",
    "next_actions": [
      {
        "command": "seo-research fetch-pages --source-set current --json",
        "reason": "Open the top authoritative sources from this wave."
      }
    ],
    "recommended_queries": [
      {
        "query": "agentic cli seo workflow examples",
        "reason": "Fill the CLI implementation gap",
        "confidence": 0.81
      }
    ],
    "stop_conditions": [
      "Stop after 12 total searches.",
      "Stop if two consecutive waves add no novel high-quality domains."
    ],
    "actions_taken": [
      {
        "type": "internal_planner_turn",
        "purpose": "derive next-query candidates from current SERP"
      }
    ]
  },
  "error": null,
  "schema_version": "v1"
}
```

Why it matters:

- The agent sees the answer and the continuation frontier in one parseable envelope.
- It removes a class of low-signal turns where the model asks itself what to do next.
- The CLI becomes agentic without becoming opaque.

Design rules:

- Put steering in `guidance`, not mixed into `result`.
- Use ranked `recommended_queries` or `next_actions`, not one vague paragraph.
- Distinguish `actions_taken` from `next_actions`.
- Keep the same field names across commands so the agent learns the contract once.

The pattern is strongest for research and SEO CLIs, where the job is not "return results" but "advance the search frontier". For repair loops the same idea appears as `next_action` and `finalize_command`; see `iterative-repair.md`.

<!-- src: audit-agentic-cli/references/agent-integration.md#17. Planner-in-the-CLI Is Valid if It Is Bounded and Disclosed -->
## A bounded, disclosed planner in the CLI

Agentic continuation is not only for MCP. A CLI can spend a small internal planning budget and return better follow-up guidance:

```bash
seo-research serp "technical seo agent workflows" --json --plan-next 3
```

The command can:

1. fetch the current SERP;
2. run a bounded internal model or heuristic planner;
3. return the current results plus the best next three queries.

This is valid when:

- the workflow is read-only;
- the continuation budget is bounded;
- the command reports what it already did (`actions_taken`);
- the output stays machine-readable.

Do not hide writes, destructive actions or expensive unbounded loops behind `--plan-next`. Use planner turns to collapse obvious research loops, not to make the CLI inscrutable.
