# Iterative Repair-Loop CLIs

> Read when: the CLI expects an agent to submit an artifact, get structured corrections, and resubmit until it is accepted, or you are auditing such a CLI.

Staged workflow, artifact channel and validation rules are in `iterative-repair-design.md`. This goes beyond `--json`: the CLI actively guides the agent through repeated improvement cycles. It does not just say "failed". It explains what is wrong, what can be retried, what to fix next, and when the workflow may move to the next stage.

<!-- src: audit-agentic-cli/references/iterative-cli.md#1. When To Use Iterative CLI -->
## When to use it

Use it when the CLI expects the agent to:

- generate an artifact and submit it back for validation;
- repair invalid output over multiple attempts;
- work through a staged workflow such as `init`, `fetch`, `submit`, `status`, `finalize`;
- handle partial progress rather than all-or-nothing success.

Strong fits: localization or translation work, code generation with validation gates, manifest/schema/migration generation, patch/diff/batch-edit workflows, import or sync tools that process work in chunks.

Avoid it for trivial one-shot lookups. One-shot `read`, `list`, `get`, `status` or `whoami` commands return the simpler JSON envelope from `envelope-and-errors.md`. Do not add sessions, staged commands or retry budgets when there is no artifact to repair.

<!-- src: audit-agentic-cli/references/iterative-cli.md#2. The Semantic Shift -->
## The semantic shift

Machine-readable output is necessary but not sufficient for work that improves over time. An iterative CLI treats the command surface as a protocol with feedback:

1. the agent proposes work;
2. the CLI validates it;
3. the CLI returns structured correction guidance;
4. the agent repairs the artifact;
5. the workflow advances only when the artifact is acceptable.

The CLI becomes a collaborator rather than a passive validator.

<!-- src: audit-agentic-cli/references/iterative-cli.md#3. Core Response Requirements -->
## Core response requirements

Every response should make these questions easy to answer:

1. What stage am I in?
2. Did the last step succeed, fail, or partially succeed?
3. What exactly is wrong?
4. Is retrying allowed, and how many attempts remain?
5. What should I run next?
6. How close am I to completion?

Recommended fields:

```json
{
  "ok": false,
  "phase": "submit_patch",
  "progress": {"completed": 3, "total": 10, "percent": 30.0},
  "next_action": {
    "action": "retry",
    "command": "mycli submit --session session.json --batch 4 --patch batch_4.patch",
    "description": "Fix the invalid entries and resubmit batch 4"
  },
  "attempt": 2,
  "max_attempts": 3,
  "validation_errors": [
    {
      "scope": "entry",
      "id": "entry-49",
      "code": "MISSING_PLACEHOLDER",
      "message": "Placeholder %d was removed",
      "suggestion": "Preserve %d exactly in the translated line"
    }
  ]
}
```

The exact shape can vary; the semantics should not.

<!-- src: audit-agentic-cli/references/iterative-cli.md#Minimal repair-loop response contract -->
## Minimal repair-loop contract

The smallest contract for generated-artifact repair loops:

```json
{
  "ok": false,
  "phase": "submit",
  "artifact_ref": "batch_4.patch",
  "accepted": false,
  "validation_errors": [],
  "warnings": [],
  "attempt": 2,
  "max_attempts": 3,
  "progress": {"completed": 3, "total": 10, "percent": 30},
  "next_action": {
    "command": "mycli submit --session session.json --artifact batch_4.patch",
    "reason": "Repair validation errors and resubmit the same artifact."
  },
  "finalize_command": null
}
```

When `accepted` becomes `true`, return either the next artifact command or a concrete `finalize_command`.

<!-- src: audit-agentic-cli/references/iterative-cli.md#4. What Makes The Feedback High Quality -->
## What makes feedback high quality

Feedback is specific enough to repair without guessing, aggregated enough to avoid one-error-at-a-time thrash, stable enough to script against, and actionable enough to name the next move. It usually includes: the failed batch, item, resource, line or identifier; a typed error code; a concise explanation; a concrete fix suggestion; retryability and the attempt budget; the next command or action.

Bad feedback: `invalid input`; `something went wrong`; exit code `1` with no body; interactive prompts asking the operator how to recover.

<!-- src: audit-agentic-cli/references/iterative-cli.md#Repairable vs escalation-needed failures -->
## Repairable vs escalation-needed

| Class | Examples | CLI response |
|---|---|---|
| Repairable | Missing placeholder, invalid JSON field, patch hunk mismatch, untranslated segment, schema violation with item IDs | Return stable error codes, exact locations or IDs, suggestions, retry budget, and the same submit command. |
| Escalation-needed | Subjective quality judgment with no criteria, missing source context, auth or permission denial, external service outage, destructive conflict requiring human policy | Stop the repair loop, mark `accepted: false`, set `next_action` to escalation or prerequisite resolution, and avoid inventing fixes. |

<!-- src: audit-agentic-cli/references/iterative-cli.md#9. Anti-Patterns -->
## Anti-patterns

- Returning only `success` or `failure` without stage information.
- Emitting human explanations without machine codes.
- Using the same exit code for usage mistakes, validation errors and transient failures.
- Prompting interactively during a repair loop.
- Throwing away session state after a failed attempt.
- Accepting partial work silently without reporting what was skipped.
- Requiring the agent to infer the next command from narrative text.

<!-- src: audit-agentic-cli/references/iterative-cli.md#10. Checklist -->
## Checklist

Before calling a repair-loop CLI agent-ready, verify that it:

- exposes stable machine-readable responses for every stage;
- reports exact repair targets, not generic failure;
- distinguishes retryable and non-retryable outcomes;
- provides progress and next-step guidance;
- preserves enough session state to resume safely;
- supports deterministic completion through an explicit finalization step.
