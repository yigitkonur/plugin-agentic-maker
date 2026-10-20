# Runner: headless (the default)

> Read when: you start fresh workers with `agentic-maker run`, or you are replacing the old synthetic-subagent test, the launch script or the trace parser.

<!-- src: audit-skill-by-derailment/SKILL.md#Mode A: Synthetic Subagent Execution -->
The old "Mode A" was a fast in-process simulation run by a subagent that shared the parent's skills and settings. That is not a fresh session, so it is replaced by a real fresh process in a clean room ([clean-room](../clean-room.md)). The cheap smoke check survives as `run <scenario> --dry-run` (plan only) and a small scenario with `max_turns: 8`.

1. Write a prompt with everyday user energy and two or three implicit constraints ([scenarios](../scenarios.md)).
2. `agentic-maker run <scenario> --session ${CLAUDE_SESSION_ID}` launches the worker, waits (the scenario's `timeout_s`), and writes the take directory.
3. Read the trace: `trace.md` and `trace.norm.jsonl` are produced for you.
4. Apply the fix patterns for the root causes found (`derailment-method/references/fix-patterns.md`).

## What a take directory holds

`prompt.txt`, `stream.jsonl` (the raw record), `stderr.txt`, `trace.norm.jsonl`, `trace.md`, `env.json` (what the worker could see), `run.json` (command, exposure, workspace, seed manifest, status, cost), later `receipts.json` and `findings/`. The worker's workspace is a temp directory recorded in `run.json`.

## Statuses and exit codes

`status`: `completed`, `max_turns`, `budget`, `timeout`, `error`. A natural finish exits **0**; any other status exits **8** (partial: the trace was kept and is still evidence). A worker that produced no usable record exits **7** (dependency_failed) with its stderr.

<!-- src: audit-skill-by-derailment/scripts/launch-derailment.sh.md#launch-derailment.sh -->
## Replacing `launch-derailment.sh`
The old script rendered the worker's prompt and optionally piped it to a configured agent command. `run` renders the prompt from the scenario - **without** the old sentence that handed the worker the skill's path - and launches `claude` itself.

<!-- src: audit-skill-by-derailment/scripts/launch-derailment.sh.md#Usage -->
### Usage
`agentic-maker run <scenario.md> [--runner headless] [--run-id ID] [--session ID] [--dry-run] [--self-annotate]`. The old `--skill-path` and `--task` become the scenario's `target` and `## Prompt`; `--round` becomes the run id and take number; `--trace-out` is the take directory; `--agent-cmd` is replaced by the verified recipe.

<!-- src: audit-skill-by-derailment/scripts/launch-derailment.sh.md#Examples -->
### Examples
```
agentic-maker run .agentic-maker/scenarios/typed-client.md --dry-run
agentic-maker run .agentic-maker/scenarios/typed-client.md --session "$CLAUDE_SESSION_ID"
agentic-maker run .agentic-maker/scenarios/typed-client.md --self-annotate     # biased, cheap
```
`--self-annotate` appends the old marker request (`[STUCK] [GUESSED] [BROKE] [NICE]`) to the prompt. It changes what the worker does and what it reports, so use it only as a quick smoke test; the reader assigns markers from the trace in normal runs.

<!-- src: audit-skill-by-derailment/scripts/launch-derailment.sh.md#Exit codes -->
### Exit codes
| Code | Meaning |
|---|---|
| 0 | the worker finished normally |
| 2 | bad arguments (the old script's 2) |
| 3 | scenario, target, binary or record not found |
| 6 | scenario invalid, fixture script failed |
| 7 | the worker produced no usable record |
| 8 | the run ended as max_turns / budget / timeout; trace kept |

<!-- src: audit-skill-by-derailment/scripts/parse-derailment-trace.sh.md#parse-derailment-trace.sh -->
## Replacing `parse-derailment-trace.sh`
`agentic-maker normalize` reads Claude `stream-json` and Claude session transcripts and writes `trace.norm.jsonl` and `trace.md`. Unlike the old parser it never drops silently: `ignored` counts what it skipped on purpose, `unknown` counts event types it does not know, `unparsed` counts lines that were not JSON. A file that is not JSON at all is kept as a terminal capture, one `screen` event per line.

<!-- src: audit-skill-by-derailment/scripts/parse-derailment-trace.sh.md#Usage -->
### Usage
`agentic-maker normalize <take dir | file> [--out DIR]`. There is no `--context N`: the reader pulls context with `Read` on `trace.norm.jsonl`.

<!-- src: audit-skill-by-derailment/scripts/parse-derailment-trace.sh.md#Output -->
### Output
Counts of events, tool calls, tool errors, permission denials, cost, turns, and the files written. Marker counts exist only for runs started with `--self-annotate`; otherwise markers come from the reader's findings.

<!-- src: audit-skill-by-derailment/scripts/parse-derailment-trace.sh.md#Examples -->
### Examples
```
agentic-maker normalize .agentic-maker/runs/r1/typed-client/01
agentic-maker normalize ~/.claude/projects/<cwd>/<session>.jsonl --out /tmp/session-trace
```

<!-- src: audit-skill-by-derailment/scripts/parse-derailment-trace.sh.md#Exit codes -->
### Exit codes
0 parsed; 2 usage; 3 file not found; 6 the file holds no events at all (`empty_trace`).
