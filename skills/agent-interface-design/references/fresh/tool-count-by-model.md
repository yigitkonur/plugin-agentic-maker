---
as_of: 2026-04-14
verify_before_citing: true
---

# Tool-count limits by model and client

> Read when: you need the per-model "sweet spot" or active-tool cap for a specific model, or a client's hard tool cap, to apply the cues in `decisions/tool-count.md`.

Moved here from the tool-count decision tree because model names and limits go stale. The tree gave no date; the superseding vendor guidance in `fresh/model-behavior.md` is dated 2026-04-14.

## Per-model sweet spots (tool-count decision tree)

| Model | Sweet spot | Active-set cap (20-40 tools branch) |
|---|---|---|
| Gemini 1.5 Pro | about 10; consider pruning or grouping | cap active set at 10 |
| GPT-4 / 4.1 | 15-20; at the limit when you have 20 | cap active set at 20 |
| Claude 3.5 / 4 | 20-30; still safe | cap active set at 30 |

## Conflicts

- The table above is the older per-model rule. `fresh/model-behavior-rules-tool-surface.md` (Rule 1) supersedes it: cap active tools at 20 regardless of vendor, because OpenAI recommends fewer than 20, Google recommends 10-20, and Microsoft Research measured up to 85% accuracy loss from tool-space interference.

> Note: `decisions/tool-count.md` uses one ladder (up to 20 active tools is comfortable (register them eagerly); past about 20, expose only the tools the task needs (groups or session unlocking); about 30 is a warning; 40 or more needs meta-tools (list, describe, execute)) and treats both the per-model table and the 20-tool cap as diagnostic cues.

## Client tool caps

Cursor enforced a 40-tool cap until 2025-09, then 80; Windsurf documents 100; Claude Code has no cap but pays context cost. Details and sources: `fresh/client-compatibility-content-and-tools.md` (Pattern 2).
