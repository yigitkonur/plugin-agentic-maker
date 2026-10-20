# Runner: existing (read sessions that already happened)

> Read when: you audit a skill or tool from sessions you or a fleet already ran - other repos, other harnesses, a live pane you must not disturb.

<!-- src: audit-skill-by-derailment/SKILL.md#Mode B: Live Herdr Multi-Pane Fleet Audit | audit-skill-by-derailment/references/herdr-pane-audit.md#Herdr Multi-Pane Live Session Audit & Agent Fleet Coordination -->
This is the old "Mode B". Nothing is launched: `agentic-maker run <scenario> --runner existing --from <record>` copies the record into a take directory, normalizes it and writes the same `env.json`, `run.json`, `trace.md`, so the reader and every check work unchanged. A fleet audit repeats the ingest per record, then merges the findings ([synthesis-matrix](../synthesis-matrix.md)).

Two honest limits: a session transcript has no `init` event, so what the agent could see is **unknown** (`env.json` says so); and without a seeded workspace the Receipts cannot run unless you pass `--workspace <dir>` for the directory the agent worked in.

<!-- src: audit-skill-by-derailment/references/herdr-pane-audit.md#1. When to Use Mode B (Herdr Multi-Pane Audit) -->
## When to use it

- you are given sessions or panes to audit (live or finished);
- you want real traces across several repositories or worktrees at once;
- you want to compare how different models (Claude, Codex, other harnesses) read the same text;
- you need the run to be exactly what the user ran, not a staged one.

<!-- src: audit-skill-by-derailment/references/herdr-pane-audit.md#2. Herdr CLI Discovery & Scrollback Retrieval -->
## Where the record is, best source first

1. **Claude session transcript:** `~/.claude/projects/<cwd with / as ->/<session-id>.jsonl`. The session id comes from the run, from a hook payload's `transcript_path`, or from `herdr agent get <agent>` -> `.result.agent.agent_session.value`.
2. **Codex rollout:** `~/.codex/sessions/YYYY/MM/DD/rollout-<timestamp>-<uuid>.jsonl`.
3. **Terminal scrollback** for harnesses with no readable record (and as a cross-check): `herdr agent read <agent> --source recent-unwrapped --lines 500 > capture.txt`, then `--from capture.txt`. Scrollback is weaker evidence (see [trace-sources](../trace-sources.md)).

**agy is never launched by this plugin** - a launch can have effects the plugin cannot see (which account, which quota). Audit an agy session the user already runs by reading its scrollback.

<!-- src: audit-skill-by-derailment/references/herdr-pane-audit.md#Discovery Commands -->
### Finding panes
`herdr` owns its own syntax; ask it (`herdr --help`, `herdr agent --help`) or follow the herdr-conductor skill if installed. The questions you need answered: which workspaces and agents exist, which pane is which agent, and what its harness session id is.

<!-- src: audit-skill-by-derailment/references/herdr-pane-audit.md#Scrollback Retrieval Commands -->
### Reading scrollback
`recent-unwrapped` joins soft-wrapped lines, which keeps long commands and JSON on one line. `visible` is only the screen. Capture to a file, then ingest the file; do not paste scrollback into the conversation.

<!-- src: audit-skill-by-derailment/references/herdr-pane-audit.md#4. Live Agent Fleet Coordination (Prompting Running Agents) -->
## Prompting a live agent: only after capture

Never prompt an agent while you are capturing its run - the prompt becomes part of the evidence. If the audit shows an active agent stopped early and the user wants the work finished, a corrective prompt is allowed **after** the capture is complete.

<!-- src: audit-skill-by-derailment/references/herdr-pane-audit.md#Step 1: Check Agent Readiness -->
1. Confirm the agent is idle or done before prompting (its state, not a guess).

<!-- src: audit-skill-by-derailment/references/herdr-pane-audit.md#Step 2: Dispatch Targeted Corrective Prompt -->
2. Send one specific, self-contained instruction naming the missing deliverable and how to verify it. One command, one reply; do not chain.

<!-- src: audit-skill-by-derailment/references/herdr-pane-audit.md#Step 3: Monitor Execution -->
3. Wait for the state change with a single background wait; do not poll. Read the result from the machine (files, exit codes), not from the agent's report.

<!-- src: audit-skill-by-derailment/scripts/audit-worker-pane.sh.md#audit-worker-pane.sh -->
## Replacing `audit-worker-pane.sh`
The script extracted scrollback, crash lines, tool commands, thoughts and a media-file artifact table from one pane. The parts survive as: scrollback capture (above), `normalize` (tool calls, errors, exit codes), `check receipts` (disk verification for any artifact kind). The media-type table and the result-delimiter extraction were specific to a video skill and are dropped.

<!-- src: audit-skill-by-derailment/scripts/audit-worker-pane.sh.md#Usage -->
### Usage
The old `bash scripts/audit-worker-pane.sh <pane-id> -d <output-dir>` becomes: capture the pane, `run --runner existing --from capture.txt --workspace <output-dir>`, then `check receipts`.

<!-- src: audit-skill-by-derailment/scripts/audit-worker-pane.sh.md#Arguments -->
### Arguments
`<pane-id>` -> the agent or pane you capture; `--workspace` replaces the old output-dir argument.

<!-- src: audit-skill-by-derailment/scripts/audit-worker-pane.sh.md#Options -->
### Options
`--lines N` -> the capture's `--lines`; `--thoughts` and `--tools` -> `normalize` records thinking blocks and every tool call; `--receipts` -> `check receipts`.

<!-- src: audit-skill-by-derailment/scripts/audit-worker-pane.sh.md#Output -->
### Output
Registration metadata, crash lines, tool commands, receipts and the artifact check are now `env.json`, `trace.md`, `receipts.json`.

<!-- src: audit-skill-by-derailment/scripts/read-herdr-panes.sh.md#`read-herdr-panes.sh` -->
## Replacing `read-herdr-panes.sh`
It read and formatted scrollback and thought blocks from several panes. Capture each pane to a file and ingest each as its own take.

<!-- src: audit-skill-by-derailment/scripts/read-herdr-panes.sh.md#Usage -->
### Usage
One capture and one `run --runner existing` per pane.

<!-- src: audit-skill-by-derailment/scripts/read-herdr-panes.sh.md#Options -->
### Options
`--lines` and `--source` map to the capture command; `--thoughts` / `--tools` are what `normalize` extracts from structured records (thinking text is usually not exposed - see `derailment-method`).

<!-- src: audit-skill-by-derailment/scripts/read-herdr-panes.sh.md#Examples -->
### Examples
```
herdr agent read <agent> --source recent-unwrapped --lines 400 > /tmp/pane-a.txt
agentic-maker run .agentic-maker/scenarios/typed-client.md --runner existing --from /tmp/pane-a.txt
```
