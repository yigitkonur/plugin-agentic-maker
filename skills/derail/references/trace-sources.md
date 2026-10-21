# Trace sources: what to read, and what `Ctrl+O` is

> Read when: you decide which record of a run to analyse, a source is missing, or you wonder whether to toggle a verbose view.

<!-- src: audit-skill-by-derailment/references/ctrl-o-verbose-physics.md#AGY Terminal TUI Physics & The Ctrl+O Verbose Audit Protocol -->
The rule behind `Ctrl+O` is **never judge from a view that hides what the agent did**. A terminal view that folds tool arguments, reasoning and output is such a view. One keystroke answers it for one harness; a ranking of sources by trust answers it everywhere, because most harnesses leave a better record than their screen.

## The ladder

1. **A structured record the harness wrote.** Claude: `claude -p --output-format stream-json` (what `run` uses), or the session transcript `~/.claude/projects/<cwd with / as ->/<session>.jsonl` (its path is in every hook payload as `transcript_path`, and under herdr in `agent get` -> `agent_session.value`). Codex: `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`. agy: `~/.gemini/antigravity-cli/brain/<id>/.system_generated/logs/transcript_full.jsonl`. Give `normalize` or `run --runner existing --from` the id (`session:<id>`) or the herdr pane (`herdr:<pane>`) instead of the path; the same files read with plain `jq`: [session-recipes](session-recipes.md). These carry every tool call with full arguments, every result, hook events. The Claude transcript format is internal and can change between versions: `normalize` is tolerant and reports what it did not understand.
2. **Terminal scrollback**, taken with `recent-unwrapped`. Weaker: it contains only what the screen showed. If the view is folded, unfold it before capturing (below).
3. **The agent's own report.** A claim; never evidence.

`agentic-maker normalize` turns 1 and 2 into the same `trace.norm.jsonl` and `trace.md`; a capture becomes one `screen` event per line, and a finding that rests on one says so.

<!-- src: audit-skill-by-derailment/references/ctrl-o-verbose-physics.md#1. The Anatomy of AGY TUI Rendering -->
## What folded views hide

An interactive TUI folds its own activity for human readers.

<!-- src: audit-skill-by-derailment/references/ctrl-o-verbose-physics.md#Collapsed Standard View (Default) -->
In antigravity's CLI (agy) the default view shows a thought as a one-line badge (`▸ Thought (12s)`), a tool call as a status pill with the flags hidden, and command output suppressed or cut to the last lines; model answers render as Markdown.

<!-- src: audit-skill-by-derailment/references/ctrl-o-verbose-physics.md#Why Standard View Blinds Forensic Audits -->
A reader of that scrollback cannot tell whether the agent ran the right flags, cannot see a stack trace behind "Command finished", and cannot tell a confused agent from a lucky guess.

<!-- src: audit-skill-by-derailment/references/ctrl-o-verbose-physics.md#2. The `Ctrl+O` Verbose Mode Invariant -->
## `Ctrl+O`, per harness (observations, dated)

`Ctrl+O` is a *toggle*, and it means different things in different harnesses. Sending it blind can fold a view that was already open.

| Harness | What `Ctrl+O` does | Source |
|---|---|---|
| agy | unfolds thoughts, full command lines and raw output ("verbose view") | not re-tested here (agy is never launched by this plugin) |
| Claude Code | toggles a detailed transcript view: observed in a herdr pane on 2026-10-20 - folded tool output ends with "… +12 lines (ctrl+o to expand)"; after `ctrl+o` the footer reads "Showing detailed transcript · ctrl+o to toggle · ctrl+e to show all", and a second `ctrl+o` returned to the normal view (`ctrl+e` shows all) | observed, herdr 0.9.5, claude 2.1.302; documented as the transcript viewer |
| Codex | not verified | - |

Do not assume the table is current; the rule is conditional. **Probe, then toggle, then probe again**: look for expanded-output markers in a scrollback capture first; send `ctrl+o` only if the capture is collapsed; capture again and confirm.

<!-- src: audit-skill-by-derailment/references/ctrl-o-verbose-physics.md#What Verbose Mode Exposes in Terminal Scrollback -->
## What the verbose view shows (agy)

Expanded reasoning ("Thinking Process: ..."), the exact tool call with the full command line, and raw stdout and stderr including the line `Process exited with code N`. These are what findings need: arguments, results, exit codes.

<!-- src: audit-skill-by-derailment/references/ctrl-o-verbose-physics.md#3. Automating `Ctrl+O` via Herdr -->
## Sending the key under herdr

<!-- src: audit-skill-by-derailment/references/ctrl-o-verbose-physics.md#Interactive Injection -->
`herdr agent send-keys <agent> ctrl+o` (or `pane send-keys`) sends it. Only to a worker pane this run created, never to this session's own pane.

<!-- src: audit-skill-by-derailment/references/ctrl-o-verbose-physics.md#Verifying Verbose Mode in Scrollback -->
Verify by reading a capture and grepping for expanded markers (`Thinking Process:`, `CommandLine:`, `Tool:`) instead of folded badges (`▸ Thought`). If only badges appear, toggle once and capture again.

<!-- src: audit-skill-by-derailment/references/ctrl-o-verbose-physics.md#4. Scrollback Extraction with Soft-Wrap Joining -->
## Soft-wrap joining

Terminals insert hard newlines when text exceeds the width, which breaks long commands and JSON across lines.

<!-- src: audit-skill-by-derailment/references/ctrl-o-verbose-physics.md#Always Use `--source recent-unwrapped` -->
Always capture with `--source recent-unwrapped` (it re-joins soft-wrapped lines). `visible` splits at the window width and is for looking, not parsing.

<!-- src: audit-skill-by-derailment/references/ctrl-o-verbose-physics.md#Pattern Matching on Unwrapped Streams -->
Once unwrapped, ordinary tools find what you need: tool command lines, error text and non-zero exits (`exited with code [1-9]`, `Error:`, `Exception`), and any receipt you asked the worker to print. For a structured record the same questions are answered by `trace.norm.jsonl` (`kind`, `name`, `is_error`, `exit`), which is exact; prefer it.
