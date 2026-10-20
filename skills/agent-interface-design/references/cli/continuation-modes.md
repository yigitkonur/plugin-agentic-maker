# Continuation Modes

> Read when: a research or SEO style CLI needs more than one search wave and the agent should be told what to do next.

<!-- src: audit-agentic-cli/references/execution-patterns.md#16. Continuation Modes for Research and SEO CLIs -->
## Modes

Research and SEO workflows often need more than one search wave. Apply the steering lessons from tool-output design to CLI design by making continuation an explicit execution mode, not an accidental side effect. The steering text is the strongest lever and also an injection surface; read `../decisions/steering-contract.md` before putting guidance in output.

| Mode | What it does | When to use |
|---|---|---|
| `none` | Return current results only | Default, lowest surprise |
| `suggest` | Return current results plus recommended next queries/actions | Best default for agent use |
| `prefetch` | Execute a bounded next wave and return both current and prefetched results | Read-only research loops with strong evals |
| `closed-loop` | Continue until stop conditions fire | Only in secure, bounded, well-observed environments |

> Reconciled: the mode table calls `none` the default ("lowest surprise") and `suggest` the best choice for an agent, while the rules said "Default to `suggest`". The flag default is `none`; an agent caller opts in with `--continuation-mode suggest`.

Example flags:

```bash
seo-research serp "technical seo agent workflows" --json --continuation-mode suggest --plan-next 3
seo-research serp "technical seo agent workflows" --json --continuation-mode prefetch --plan-next 2 --max-waves 2 --budget-queries 8
```

## Response shape

```json
{
  "ok": true,
  "result": {
    "seed_query": "technical seo agent workflows",
    "results": ["..."]
  },
  "_agent_guidance": {
    "source": "seo-research",
    "recommended_queries": [
      {
        "query": "agentic cli seo workflow examples",
        "reason": "Current wave lacks concrete CLI implementation detail"
      }
    ],
    "stop_conditions": [
      "Stop after 12 total searches",
      "Stop if two consecutive waves add no novel authoritative domains"
    ],
    "actions_taken": [
      { "type": "internal_planner_turn", "purpose": "derive next-query frontier" }
    ],
    "budget_remaining": { "queries": 5, "waves": 1 }
  },
  "error": null
}
```

## Operational rules

- When an agent opts in, choose `suggest` before `closed-loop`; the flag default stays `none`.
- Cap waves, queries, time, and spend.
- Keep continuation read-only unless the user explicitly asked for automation beyond planning.
- Emit `actions_taken`, `budget_remaining`, and `stop_conditions` every time.
- Make planner output reproducible enough to evaluate.

The command should not just return the present state; it should expose the next frontier in a stable contract. Flags: `--continuation-mode`, `--plan-next`, `--max-waves`, `--budget-queries`, `--emit-guidance`. For the next-action fields of a repair loop, see `repair-build-order.md`.
