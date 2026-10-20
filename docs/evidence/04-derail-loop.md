# Evidence, ledger row 4: the derail loop on a skill that is broken on purpose

Recorded 2026-10-20 on Claude Code 2.1.302 (subscription login). The target is `fixtures/skill-project/skills/manifest-synth`, a small skill with planted defects: a jargon description and an opaque name (nothing a user would say), a script path relative to the skill directory instead of the working directory, a reference path with a typo (`reference/` for `references/`), and "keep each entry short" with no number. The scenario is `release-notes.md`: an everyday request that never names the skill, with eleven receipts.

An orchestrator session ran `/agentic-maker:derail skills/manifest-synth --rounds 3` with the plugin loaded in the verified clean-room recipe (`--restricted --strict-mcp-config`), so the loop itself - the skill text, the CLI, the reader, the hook - was the only thing driving it. Workers were fresh `claude -p` sessions in the same recipe.

## What the loop did (two runs of the same experiment)

| | Run 1 | Run 2 (after fixing what run 1 showed) |
|---|---|---|
| Orchestrator events / tool calls | 130 / 42 | 131 / 37 |
| Tool errors | **10** | **2** (both are the documented exit 8 "partial") |
| Permission denials | **7** | **0** |
| Orchestrator cost (estimate) | $0.41 | $0.32 |
| Take 1 | skill triggered; receipts 10/11 (the worker invented its own title) | **skill never triggered** (T1); receipts 10/11 |
| Reader findings | 5: 4 verified (S3 P0, M5 P0, M3 P1, M1 P1), 1 rejected (a P2 trigger finding whose quote is not in the cited event) | 3: 2 verified (T1 P0, S3 P1), 1 rejected (M5 P1, quote not verbatim) |
| Fix applied | rewrote `SKILL.md` (+7 / -3) | rewrote `SKILL.md` (+4 / -4), see below |
| Reruns | 2 takes, 11/11 receipts, predicates met | 2 takes, 11/11 receipts, all predicates met |
| Ledger | closed `clean`, but it watched only `scripts/group.py` | closed `clean`, watched `skills/manifest-synth` |

The two runs found different defects because the worker is not deterministic: that is why a scenario is run several times and why the loop reports a rate, not a verdict.

## The fix of run 2 (a rewrite of the controlling text, not a rule beside it)

```diff
-description: Synthesizes semver-delimited artefact manifests from VCS delta enumerations for downstream distribution channels.
+description: Use when asked to write release notes or a changelog (RELEASE_NOTES.md) from a list of commits such as commits.txt and a version number such as version.txt. Groups commits into Features / Fixes / Other and applies the project's exact release-notes format.
-# Manifest synthesis
+# Release notes from a commit list
-1. Run the grouping helper on the commit list: `python3 scripts/group.py commits.txt`.
-2. Write `RELEASE_NOTES.md` in the format described in `reference/format.md`.
+1. Run the grouping helper from the working directory that holds `commits.txt`: `python3 <skill-dir>/scripts/group.py commits.txt`, where `<skill-dir>` is this skill's directory.
+2. Read `<skill-dir>/references/format.md`, then write `RELEASE_NOTES.md` exactly in that format.
```

`agentic-maker check diff` judged it `ok: the quoted controlling text was rewritten or deleted`. The predicate for the trigger finding is `{"type": "tool_used", "tool": "Skill"}`: false on the untriggered take, true on both reruns.

## The Stop gate in the real harness

A separate session was told to open a ledger, set it to `fixing`, edit the skill's description, and answer "Fixed." without rerunning anything. The Stop hook (registered in the `derail` skill's frontmatter, `${CLAUDE_PLUGIN_ROOT}/bin/agentic-maker ledger gate`) answered:

```
{"decision": "block", "reason": "A derail fix is in flight and 3 target file(s) changed after the newest completed trace (...). Do not report this as fixed: no fresh run has seen the change. Pick one: (1) rerun the scenario ..., (2) record that it could not be verified: ..., (3) stop the loop: ..."}
```

The session then ran `ledger close --outcome unverified` and ended with "The edit is not verified, so I should not have said 'Fixed.'", after which the second Stop passed with no output. (The block message suggested `ledger --session X close`; the CLI wants `ledger close --session X`. Fixed in the same commit that added this file.)

## Friction the loop found in itself (all fixed before run 2)

| Seen in run 1 | Cause | Fix |
|---|---|---|
| `run release-notes --dry-run` -> exit 3 | `run` wanted a path; the agent gave the scenario's name | `run` accepts a bare scenario name |
| ledger opened with three file targets, not `SKILL.md` | the skill said "the files you will edit" | `--target` is the target directory; `ledger fix` also adds every controlling file |
| `sleep 60` while the reader worked | the skill did not say the reader returns in the background | "wait for its completion notice; do not sleep or poll" |
| 7 denied Bash calls | shell variables, heredocs and `&&` chains cannot be checked against allowed-tools patterns | "one command per call, literal paths"; every reply carries `next_actions` |
| a "not met" predicate on a correct rerun | the reader's predicate was a regex over one spelling of a command line | predicates test behaviour (`reads_file`, `tool_used`), never wording |
| `unknown event types: task_progress, tool_progress` | chatty harness events | counted under `ignored`, on purpose |

## Limits of this evidence

- One target, one scenario, two orchestrator runs and four worker takes per run: it shows the loop works end to end and that it finds real defects, not a recall rate.
- Thinking text was empty in every trace (`belief_source` was `inferred` throughout).
- Run 2's clean takes were judged from receipts and predicates, not re-read by the reader; the orchestrator said so in its report and closed the ledger with that caveat.
