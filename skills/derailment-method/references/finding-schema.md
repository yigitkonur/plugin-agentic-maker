# Finding schema and the reader's handback

> Read when: you are producing findings as the reader, or checking that a findings file is well-formed.

<!-- src: audit-skill-by-derailment/references/forensic-subagent-briefs.md#2. Universal Forensic Auditor Subagent Brief Template -->
The reader returns **one JSON object as its final message**. It never writes files. The orchestrator saves it as `findings/<reader>.json` and runs `agentic-maker check findings` on it; only verified findings can be fixed. This replaces the old markdown report with a pane-coordinates handback.

```json
{
  "findings": [
    {
      "id": "F1",
      "marker": "STUCK | BROKE | GUESSED | NICE",
      "severity": "P0 | P1 | P2",
      "root_code": "T1",
      "layer": "trigger | discovery | execution | recovery | completion",
      "trace_refs": [9],
      "quote": "text copied exactly from one of the cited events",
      "belief": "what the agent believed at that moment, in one sentence",
      "belief_source": "observed | inferred",
      "controlling_text": {"file": "skills/x/SKILL.md", "lines": "3", "quote": "exact sentence, or the string ABSENT"},
      "fix": {"kind": "rewrite | delete | inline-at-point-of-use | restructure | add-probe | add", "patch": "the replacement text or the change, concretely"},
      "rerun_predicate": {"type": "tool_used", "tool": "Skill"},
      "confidence": "low | medium | high"
    }
  ],
  "nice": [
    {"quote": "...", "trace_refs": [12], "controlling_text": {"file": "...", "quote": "..."}, "why": "what it prevented"}
  ],
  "dimensions_clear": ["budget", "recovery"]
}
```

## Rules that the checker enforces

- `trace_refs` are event numbers that exist; `quote` appears **verbatim** (whitespace-normalized) in the text, name or arguments of at least one cited event.
- `controlling_text.quote` appears verbatim in `controlling_text.file` - or is exactly `ABSENT`. Use `ABSENT` only when nothing in the text covers the situation; the correct fix is then an addition and `check diff` will not flag it.
- `root_code` is one of the codes in [taxonomy](taxonomy.md).
- `belief_source` is `observed` only if a cited event carries reasoning text; otherwise `inferred`.
- ids are unique.

## `rerun_predicate`: how the next run will be judged

A predicate is a machine-checkable test over the next run's trace, stated before the fix. Write it about **behaviour** - was the skill used, was the file opened, did a command exit 0 - and not about the exact wording of a command line or a message, which a correct run may phrase differently (`python3 -I /abs/path/scripts/x.py` and `python3 scripts/x.py` are the same behaviour).

| `type` | Fields | Passes when |
|---|---|---|
| `tool_used` | `tool`, optional `input_match` | the tool (for a skill: `Skill` with the skill's name in the input) was called |
| `regex` | `pattern` | the pattern matches the trace text |
| `not_regex` | `pattern` | it does not |
| `order` | `before`, `after` | the first matching `before` call precedes the first matching `after` call |
| `reads_file` | `path` | the agent opened that file |
| `exit_code` | `command`, `equals` | a matching command exited with that code |
| `judged` | `criteria` | a person or model judges it; allowed, labelled, and never a clean pass on its own |

<!-- src: audit-skill-by-derailment/references/forensic-subagent-briefs.md#1. The Two-Tier Architecture Overview -->
## The two tiers

- **Tier 1, the worker:** a fresh agent in a clean room doing a realistic task from a prompt that does not name the target. Its record is the evidence.
- **Tier 2, the reader:** a read-only agent (`Read`, `Grep`, `Glob`) that gets `trace.md`, `trace.norm.jsonl` and `receipts.json`, cross-checks the trace against the receipts, and returns findings. It cannot run commands or edit files; anything that needs the disk is precomputed by `check receipts`.

The orchestrator is the only writer: it verifies, rewrites the controlling text, checks the applied diff, reruns in a fresh session and judges with the predicate.
