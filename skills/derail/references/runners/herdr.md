# Runner: herdr (a live, interactive worker)

> Read when: the scenario needs what a person would see - trust dialogs, approvals, multi-turn, the real TUI - or the user asks for a live round. Status: watched working on herdr 0.9.5 with a Claude worker (2026-10-20): the sequence below ran as written; evidence in `docs/evidence/07-live-herdr.md`. Codex and agy workers were not started.

<!-- src: audit-skill-by-derailment/references/herdr-native-runner.md#Herdr Native Runner & CLI Orchestration Guide -->
herdr is a terminal workspace manager that runs coding agents in tabs and panes and reports their state (`idle`, `working`, `blocked`, `done`). This plugin does **not** re-document herdr. If the `herdr-conductor` plugin is installed, follow its `herdr` skill for syntax and rules; otherwise `herdr --help`, `herdr agent --help` and `herdr --skill` are the authority. What follows is only what a derailment round needs and where it differs from the old runner guide.

## The rules that matter here (from herdr-conductor)

- **Never poll.** No loop of `agent get` / `agent read`, no `sleep` loops. One command, read its reply, choose the next. Waiting is one `agent wait` (foreground with its own `--timeout`, or one background wait) and the session is woken when it exits.
- **Never touch this session's own pane.** Inside herdr (`HERDR_ENV=1`) the caller's pane is yours: never prompt it, send it keys or close it. Create a new tab for the worker.
- **Interactive agents only via `agent start`.** Never `claude -p` / `codex exec` / `agy -p` for a herdr worker. (The headless runner is a different mechanism with its own exit code and is not under herdr.)
- **`--no-focus` on everything you create.** The user's herdr is live.
- **The agent's report is a claim; the machine is the witness.** Verify with files and exit codes.
- **agy is never started by this plugin** (its command may be a wrapper that rotates accounts at every launch). Use agy only when the user already runs one, through the `existing` runner.

<!-- src: audit-skill-by-derailment/references/herdr-native-runner.md#1. Pre-Flight Environment & Session Verification -->
## 1. Before you start

`HERDR_ENV=1` means "this process runs inside a herdr pane"; herdr also sets `HERDR_PANE_ID`, `HERDR_TAB_ID`, `HERDR_WORKSPACE_ID`, `HERDR_SOCKET_PATH`. `herdr pane current --current` resolves your own pane (read it, never act on it). Outside herdr, give every command an explicit id: an omitted target can fall back to the pane the user is focused on.

<!-- src: audit-skill-by-derailment/references/herdr-native-runner.md#2. Workspace & Tab Lifecycle Management -->
## 2. Tab lifecycle

<!-- src: audit-skill-by-derailment/references/herdr-native-runner.md#List Active Workspaces & Panes -->
List workspaces, panes and agents only to find ids; the replies already carry them.

<!-- src: audit-skill-by-derailment/references/herdr-native-runner.md#Create a Dedicated Workspace -->
Prefer a new tab in the current workspace over a new workspace; a workspace is only needed if the user wants the round isolated.

<!-- src: audit-skill-by-derailment/references/herdr-native-runner.md#Create a Tab & Resolve its Pane ID -->
Prepare first: `agentic-maker run <scenario> --prepare` seeds the workspace, writes the wrapper plugin and prints the exact `claude_args`, the prompt and a `session_id`; it launches nothing (`--workspace-dir <dir>` reuses one scratch directory, so the trust dialog below is answered once). Then `herdr tab create --workspace <w> --cwd <the prepared workspace> --label derail-<name> --no-focus`. Take the ids from the reply: `.result.tab.tab_id` and `.result.root_pane.pane_id` (observed on 0.9.5; the old guide's `.result.pane.id` does not exist). The tab's cwd is the seeded temp workspace from `run`'s fixtures, never the target project.

<!-- src: audit-skill-by-derailment/references/herdr-native-runner.md#3. Launching Worker Agents (`herdr agent start`) -->
## 3. Start the worker

`herdr agent start <name> --kind claude --pane <pane_id> --timeout 30000 -- <claude args>`. For a clean room pass the same isolation flags as the headless recipe (`--restricted --strict-mcp-config --plugin-dir <target> --add-dir <target> --model <m>`; see [clean-room](../clean-room.md)). Then **read the screen once**: a first run in a folder stops at a trust dialog (`agent_not_ready`, observed: the screen names the workspace and offers "No, exit" / "Yes, I trust this folder"; `down`, then confirm on screen, then `enter`). Check that the folder named is the one you prepared. The answer is stored in `~/.claude.json` (`projects[<folder>].hasTrustDialogAccepted`) and outlives the run: a fresh temp directory adds one entry per round, which is why `--workspace-dir` exists. Herdr-managed claude reads the user's settings unless `--restricted` is given. Answer only dialogs listed in the scenario's `approvals:`; any other dialog is a finding (real friction for a real user) and the run ends `needs_decision`.

<!-- src: audit-skill-by-derailment/references/herdr-native-runner.md#4. Prompting Worker Agents (`herdr agent prompt`) -->
## 4. Prompt it

`herdr agent prompt <name> "<the scenario prompt, verbatim>" --wait --timeout <ms>` for a turn of a few minutes. Longer: confirm delivery (`--until working`), then one background wait. The brief is **the scenario prompt and nothing else**: no "you are a worker", no marker request, no callback instruction, and not the `herdr-worker` helper agent, which appends text of its own. Deliverables go to files in the worker's cwd.

## Continue

Reporting back, waiting, capturing the record, keys, teardown and the old step-by-step loop: [herdr-record-and-teardown](herdr-record-and-teardown.md).
