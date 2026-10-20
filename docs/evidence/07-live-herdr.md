# Evidence, ledger row 7: a live herdr round

Recorded 2026-10-20 on herdr 0.9.5 and Claude Code 2.1.302. A Claude worker, started by the `herdr-conductor` rules, ran the `release-notes` scenario against the seeded skill in a new tab of the same workspace as the session driving it. Codex and agy workers were **not** started (see the end).

## The command sequence, as run (one command, one reply, no polling)

| # | Command (shortened) | What came back |
|---|---|---|
| 1 | `agentic-maker run release-notes --prepare` | seeded workspace, wrapper plugin, the exact `claude_args`, the prompt; nothing launched |
| 2 | `herdr tab create --workspace <w> --cwd <workspace> --label am-live-1 --no-focus` | `tab_id wTG:tZ`, `root_pane.pane_id wTG:pZ` (the old guide's `.result.pane.id` does not exist) |
| 3 | `herdr agent start am-live-1 --kind claude --pane wTG:pZ --timeout 30000 -- <claude_args>` | `agent_not_ready`: "agent am-live-1 is blocked during startup" |
| 4 | `herdr agent read am-live-1 --source visible` | the trust dialog, naming the prepared folder: "No, exit" selected, "Yes, I trust this folder" |
| 5 | `herdr agent send-keys am-live-1 down`, then a visible read | "Yes" selected |
| 6 | `herdr agent send-keys am-live-1 enter`, then `agent get` and a read | `idle`; the TUI banner shows "don't ask on" and the model |
| 7 | `herdr agent prompt am-live-1 "<scenario prompt, verbatim>" --wait --timeout 300000` | one foreground wait, returned `done`, `completion_seq 487`, in about 17 s of worker time |
| 8 | `agent get`, visible read | the worker's answer on screen: it used `notes:manifest-synth`, ran the grouping script, followed the format, and pointed out the `reference/` typo in the skill |
| 9 | `herdr agent send-keys am-live-1 ctrl+o`, read; again, read | see `Ctrl+O` below |
| 10 | `agentic-maker run release-notes --runner existing --from <transcript> --workspace <workspace>` | 52 events, 10 tool calls |
| 11 | `agentic-maker check receipts <take>` | **11/11 passed** |
| 12 | `herdr tab close wTG:tZ` | `ok`; the tab list shows no `am-live` tab |

The worker's brief was the scenario prompt and nothing else: no marker request, no "you are a worker", no return address, no herdr instruction. This session's own pane was never prompted, keyed or closed.

## Findings this round produced (all fixed or documented)

- **A `--restricted` worker does not report `agent_session` to herdr** (`agent get` -> `agent_session: null`): the integration that reports it lives in the user's settings, which `--restricted` ignores. The transcript is therefore found by a session id chosen up front: `--prepare` now starts the worker with `--session-id`, and the file is `<id>.jsonl` under `~/.claude/projects/<workspace path with non-alphanumerics as ->/`.
- **Ingest needed the prepared seed manifest and the real run window.** The first ingest failed four receipts (`unchanged` x2, `no-extra-files`, `mtime-in-window`) because an `existing` record has neither. `run --runner existing --workspace <dir>` now reuses the prepared manifest and derives the window from the transcript's own timestamps; the rerun passed 11/11.
- **The trust answer outlives the round.** Accepting the dialog added `projects["<temp workspace>"].hasTrustDialogAccepted = true` to `~/.claude.json` (verified by diffing a copy taken before). Editing that file while Claude Code sessions are running risks a lost write, so it was left in place; the entry points at a deleted temp directory and is harmless. `run --prepare --workspace-dir <dir>` reuses one scratch directory so the dialog appears once instead of once per round.

## `Ctrl+O` in Claude Code (observed, U7)

Folded tool output ended with "… +12 lines (ctrl+o to expand)". After `ctrl+o` the footer read "Showing detailed transcript · ctrl+o to toggle · ctrl+e to show all  verbose"; a second `ctrl+o` returned to the normal footer. So it is a toggle; sending it blind to a view that is already expanded would collapse it. Because the structured transcript exists on disk, the loop did not need it.

## What was not done

- **Codex worker, `Ctrl+O` in Codex:** not started. It would add a trust entry to `~/.codex/config.toml` and use Codex quota for a point (the key's meaning) that the transcript source makes unnecessary. A Codex **rollout adapter** exists, built from real rollout files read from disk (`~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`, codex-cli 0.163): 189 events and 13 tool calls from one real session, no unparsed lines. It is `documented only` as a live runner.
- **agy:** never launched; its command on PATH is an account-rotating wrapper.
- One round, one worker, one scenario: it shows the sequence works under the conductor's rules and produces a record the same checks accept, not how often a live worker differs from a headless one.
