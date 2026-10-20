# Runner: herdr - waiting, the record, teardown

> Read when: the worker has its prompt and you must wait, collect the evidence, answer dialogs or clean up. Start with [herdr](herdr.md).

<!-- src: audit-skill-by-derailment/references/herdr-native-runner.md#4b. The Inter-Agent Communication & Return-Address Contract -->
## 5. Reporting back (replaces the return-address law)

The old guide had the coordinator pass its own pane id and tell the worker to run `herdr agent prompt <coordinator pane> "<report>"`. That is replaced, for three reasons: the conductor's guard hook denies a prompt aimed at the caller's own pane; a worker that must also run herdr commands is no longer behaving as a user's agent (O6); and a report is only a claim. The record is the evidence, collected by the orchestrator:

<!-- src: audit-skill-by-derailment/references/herdr-native-runner.md#1. The Coordinator Return-Address Law -->
- Do not discover or hand out the coordinator's pane id.

<!-- src: audit-skill-by-derailment/references/herdr-native-runner.md#2. Teaching Workers the Herdr Prompt Command -->
- Do not teach the worker herdr commands.

<!-- src: audit-skill-by-derailment/references/herdr-native-runner.md#3. Bi-Directional Dialogue Flow -->
- Flow: orchestrator prompts the worker -> the worker works and writes its deliverables to disk -> the orchestrator waits (below), reads the worker's record, ingests it with `run <scenario> --runner existing --from <jsonl> --workspace <dir>` (the ingest reuses the prepared seed manifest and takes the run window from the transcript's own timestamps, so `unchanged`, `no-extra-files` and `mtime-in-window` receipts work), and runs `check receipts`. The transcript is `<session_id>.jsonl` under `~/.claude/projects/<the workspace path with every non-alphanumeric character as ->/`: `--prepare` starts the worker with a known `--session-id`, because a `--restricted` worker does not report `agent_session` to herdr (observed: `agent get` showed `agent_session: null`; the hook that reports it belongs to the user settings that `--restricted` ignores).

<!-- src: audit-skill-by-derailment/references/herdr-native-runner.md#5. Detecting Task Completion (`herdr agent wait`) -->
## 6. Wait

`herdr agent wait <name> --timeout <ms>` returns when the agent reaches one of the requested states (`idle`, `done`, `blocked` by default). Run it in the background and let the completion wake the session. After it returns, read the screen once and check `completion_seq` before acting: `idle` can mean "between steps".

<!-- src: audit-skill-by-derailment/references/herdr-native-runner.md#Fallback Polling Loop (via `herdr agent list`) -->
There is no polling fallback. A lost wait is restarted; time passing is not a state change.

<!-- src: audit-skill-by-derailment/references/herdr-native-runner.md#6. Capturing Terminal Scrollback (`herdr pane read`) -->
## 7. Capture scrollback (when there is no record on disk)

`herdr agent read <name> --source recent-unwrapped --lines 500` re-joins soft wraps so commands and JSON stay on one line; that is the only source worth parsing. `visible` is just the screen. A fullscreen claude leaves only its visible rows in scrollback, so for claude read the session JSONL instead; Codex redraws a single screen, so scrollback is nearly useless there and the rollout file is the record. See [trace-sources](../trace-sources.md).

<!-- src: audit-skill-by-derailment/references/herdr-native-runner.md#7. Keystroke Injection & Interactivity (`send-keys`) -->
## 8. Keys

`agent send-keys` is for answering a dialog the scenario's `approvals:` permits. It is no longer used to toggle a verbose view: with a structured record on disk there is nothing to unfold (see trace-sources for when the scrollback fallback needs it).

<!-- src: audit-skill-by-derailment/references/herdr-native-runner.md#8. Teardown & Lifecycle Cleanup -->
## 9. Teardown

Close only the tab this run created (`herdr tab close <tab_id>`), after stopping any waiter you started on it. Look first (`agent get`): hands off a pane whose input box holds text this run did not type or that the user focused.

<!-- src: audit-skill-by-derailment/SKILL.md#Mode C: The Native Two-Tier Herdr Loop (Recommended) -->
## The loop in one view (old "Mode C")

Provision a tab -> start the worker -> prompt it with the scenario -> wait -> collect the record -> receipts -> `trace-reader` -> verified findings -> fix -> rerun. Mode C was "recommended"; here it is the **confirming** round, not the inner loop: iterate in the cheaper headless runner, then confirm once live, because a live round costs wall-clock time, runs sequentially and is only as clean as the user's herdr.

<!-- src: audit-skill-by-derailment/SKILL.md#Step 1: Provision a Dedicated Tab & Resolve Pane ID -->
**Step 1 - provision the tab:** section 2 above (new tab, `--no-focus`, ids from the reply).

<!-- src: audit-skill-by-derailment/SKILL.md#Step 2: Launch Worker Agent Engine -->
**Step 2 - launch the worker:** section 3 (`agent start`, then read the screen).

<!-- src: audit-skill-by-derailment/SKILL.md#Step 3: Discover Coordinator Return Route & Dispatch Prompt -->
**Step 3 - dispatch the prompt:** section 4. The old step added the coordinator's return address and herdr instructions to the prompt; both are removed (section 5).

<!-- src: audit-skill-by-derailment/SKILL.md#Step 4: Toggle `Ctrl+O` Verbose Mode -->
**Step 4 - verbose view:** not a step any more. Take the structured record; only if the harness has none, follow the conditional rule in trace-sources.

<!-- src: audit-skill-by-derailment/SKILL.md#Step 5: Await Worker Completion -->
**Step 5 - wait:** section 6.

<!-- src: audit-skill-by-derailment/SKILL.md#Step 6: Dispatch Tier 2 Forensic Auditor Subagent -->
**Step 6 - read:** the `trace-reader` agent (read-only, returns JSON) instead of an auditor that writes patches and messages a pane.

<!-- src: audit-skill-by-derailment/SKILL.md#Step 7: Apply Verified Patches & Clean Up -->
**Step 7 - apply and clean up:** the orchestrator applies verified fixes (SKILL.md, steps 7-8), then closes its own tab (section 9).
