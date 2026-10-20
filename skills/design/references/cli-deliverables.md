# CLI Deliverables and Design Rules

> Read when: you are about to hand back CLI work and must pick the deliverable shape (audit report, refactored contract or repair-loop design) and check the design rules.

<!-- src: audit-agentic-cli/SKILL.md#Design Rules -->
## Design rules

- One stable envelope shape across all commands.
- Stdout = data. Stderr = operator. Exit code = semantic class.
- Command names and field types stay consistent across releases.
- Destructive flows are explicit: `--yes`, `--force`, `--dry-run`.
- `--help` documents examples, output fields, and exit codes.
- For repairable workflows, return enough structure for an agent to fix and retry without human interpretation.

Details, all under `skills/agent-interface-design/references/cli/`: `envelope-and-errors.md`, `exit-codes.md`, `non-interactive.md`, `repair-build-order.md`, and the pass/fail gate `checks.md`.

<!-- src: audit-agentic-cli/SKILL.md#Output Contract (Deliverable Shape) -->
## The three deliverable shapes

Pick one based on the task.

**Audit report:** scorecard by audit dimension, severity-ranked findings, command evidence (exact safe command + observed stdout/stderr/exit), why it matters for agents, recommended fix, verification command. Workflow: `skills/audit/references/cli-audit-workflow.md`.

**Refactored CLI contract:** proposed command grammar, flags and non-interactive behavior, stdout/stderr rules, JSON envelope and stream format, exit-code map, migration notes for existing users and scripts.

**Iterative repair-loop design:** phases and command family, artifact channel, validation response shape, retry budget, `next_action.command`, finalization criteria. The loop pattern is in `skills/agent-interface-design/references/cli/repair-build-order.md`.
