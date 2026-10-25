# Evidence, round two (0.2.0)

Claude Code 2.1.304, herdr 0.9.5, macOS, 2026-10-21. Everything below was run by the author; numbers are copied from the output. Scratch work lives outside the repository (`/tmp/qc2`), run records are not committed.

## 1. Corrections to round one

### 1.1 Does the user's `CLAUDE.md` reach a worker or the reader?

Counting saved transcripts for the injected marker "Contents of `<home>/.claude/CLAUDE.md`":

```
restricted workers (am-ws-*): 0 of 38 carry the user's CLAUDE.md
in-session trace-reader subagents: 11 of 26 carry it
positive control (the interactive orchestrator transcript): 23 lines match
```

Workers are clean; the in-session reader is not. Recorded as E17 in `docs/what-is-true.md`.

### 1.2 The TypeScript and Rust samples, compiled

Round one wrote that `tsc` and `rustfmt` were not installed and left both sets "UNVERIFIED beyond a read". The statement was literally true and the conclusion was avoidable: `tsc` is one `npm install` away and `rustc`/`cargo` were present (the `rustfmt` shim exists but its component is missing: `error: 'rustfmt' is not installed for the toolchain`).

**TypeScript, 98 blocks.** `typescript` 7.0.2, `@modelcontextprotocol/sdk` 1.32.1, `zod` 4, `@types/node`, `express`, `hono`, `agents`, `@cloudflare/workers-oauth-provider` 1.2.3, `@cloudflare/workers-types`, `mcp-handler` 2.3.0, `module: nodenext`.

| | Before the edits | After |
|---|---|---|
| Blocks with a syntax error | 4 (`auth-identity.md:11`, `schema-design-portability.md:54`, `schema-design-shapes.md:94`, `tool-descriptions.md:68`; a `...` placeholder, a top-level `return`, bare object literals) | **0** |
| Every `@modelcontextprotocol/sdk` import resolves | yes | yes |

Defects found by the type check, not by reading, all fixed in the pages:

| Page | Defect |
|---|---|
| `frameworks/mcp-ts/deployment-platforms.md`, `fresh/mcp-platform-vercel.md`, `fresh/mcp-platform-picker.md` | `@vercel/mcp-adapter` on npm is a stub (0.3.2, a README that says "Package has been moved"); the live package is `mcp-handler` 2.3.0, which exports `createMcpHandler` |
| `frameworks/mcp-ts/deployment-platforms.md` | `new OAuthProvider({...})` fails to type-check with `workers-oauth-provider` 1.2.3: `resourceMetadata` is required; `createMcpHandler()` needs an initializer |
| `frameworks/node/agent-integration-frameworks.md` | `z.record(z.string())` takes two arguments in Zod 4 (`z.record(z.string(), z.string())` works in 3 and 4) |
| `frameworks/mcp-ts/agentic-patterns-serf.md` | a top-level `return` in the usage line |

Not checked in this round (done after the release, section 10): 22 third-party packages that were not installed (`openai`, `pino`, `ioredis`, `@langchain/*`, `@opentelemetry/*`, `vitest`, `@aws-sdk/client-sqs`, `@vercel/blob`, `commander`, ...): those samples are checked for syntax only. Three blocks fail for reasons that belong to the compile setup, not to the page (`Ajv` default import under `nodenext`, a Cloudflare `Message` type that shadows a placeholder, relative imports without a file extension).

**Rust, 6 blocks (4 pages).** `rustc` 1.98.1 parses all six. With `clap` 4, `serde`, `serde_json`, `thiserror` 2, `uuid`, `assert_cmd` and `predicates`, `cargo check --tests` exits 0 for the four pages once `frameworks/rust/examples-cli.md` carries its `use` lines (it had none; the types it uses are defined on `examples.md`, which the page already said).

### 1.3 The clean twin was not clean

Round one wrote that a full audit "finds 9 ordinary gaps" in the clean twin. No list of them exists in any commit. Round two ran the audit for real (`claude -p "/agentic-maker:audit clean-cli/clean-cli" --restricted ...` in a scratch directory, plugin loaded with `--plugin-dir`): 12 tool calls, $0.177, first Bash call `agentic-maker probe cli`, sentinel absent. Its report:

| # | Severity | Finding |
|---|---|---|
| F1 | High | an unknown flag is accepted and the command succeeds (`list --bogus --json` exits 0) |
| F2 | Medium | a missing argument is reported as not-found, exit 3 (`get --json`) |
| F3 | Medium | per-subcommand `--help` does not work (`list --help` lists items, `get --help` exits 3) |
| F4 | Medium | `get` returns less than `list` for the same item |
| F5 | Medium | error envelope has no `retryable` or `suggestion` |
| F6 | Low | minimal envelope (no `command`, no `meta.total_count`) |

So the false-positive control was producing true positives. The twin was rewritten (`fixtures/cli/clean-cli/clean-cli`): unknown options exit 2, per-command help, `get` returns `name`, errors carry `code`, `retryable` and `suggestion`, errors found while parsing are already JSON. Writing it, the probe caught one of my own bugs (`--bogus` before `--json` was not emitted as JSON). After the fix:

```
default probe:        0 findings (exit 0)
the audit's extra probes (--safe "list --bogus --json # expect-exit 2", "get --json # expect-exit 2", ... --sub list --sub get --sub delete):   0 findings (exit 0)
```

A full audit rerun on the final audit text is in the last section.

The same audit run broke the skill's own rule once: it put `delete 1 --dry-run` in `--safe`, and said so in its report ("against the spirit of the rule"). `delete` with a dry-run flag is a state-changing command whose flag the auditor cannot know is honoured; on `seeded-cli`, which has no dry-run, that command would have run the delete. The rule's text gave the prohibition without the reason; section 8 of this file records the rewrite.

## 2. Does the knowledge help? Baseline, before any steering text changed

Headless workers (`claude -p --restricted --strict-mcp-config`, model sonnet, 40 turns, $2 cap each), 3 samples per arm, a fresh copy of the fixture each time, an everyday prompt that names neither the plugin nor a skill. "With" loads this plugin (`--plugin-dir`); "without" is the same command without it. Graded afterwards by the plugin's own probes on what the worker left behind.

| Task | With the plugin | Without | Skill fired (with) | `agentic-maker probe` run by the worker |
|---|---|---|---|---|
| (a) `seeded-cli`: "agents keep tripping over it, make it work reliably" (pristine fixture: 11 findings, 4 High) | 2, 3, 2 findings (High 2, 2, 1) | 4, 5, 5 (High 1, 2, 2) | 3 of 3 | 0 of 3 |
| (b) build a small MCP server from `_mini.py`: search, read, delete notes | 0, 1, 0 | 0, 0, 0 | **0 of 3** | 0 of 3 |
| (c) clean up the 24-tool seeded MCP server (pristine: 16 findings, 2 High) | 0, 0, 0 | 1, 0, 4 | 3 of 3 | 0 of 3 |
| (b0) add a calendar-delete tool to a server that already has `delete_user` | all six runs copied the existing pattern: `destructiveHint: true`, a warning in the description | same | 0 of 3 | n/a |

What it says, plainly:
- On the CLI task the plugin arm ends with about half the findings (mean 2.3 against 4.7) and the same number of High ones. The `secret.argv` finding (a token documented on the command line) survives in all three plugin runs, because nobody ran the probe.
- On small MCP tasks Sonnet already builds a clean server without help; the grader cannot tell the arms apart, and on the plain "build an MCP server" request the skill did not fire at all.
- No worker in the plugin arm ran `agentic-maker probe` (0 of 9): the write-time loop (build, probe, fix) is not in the text they were given.
- Harness noise: 3 plugin-arm and 4 plugin-less runs hit one or two permission denials of compound commands (`cd ... && ...`, `for` loops, heredocs) that the allow-list did not match; the workers recovered, and both arms are affected alike.

**These numbers carry a confound** (denied compound commands, see the harness-noise bullet): they are kept as recorded, and section 7 repeats the comparison with the allow-list fixed and a third arm (the plugin as it was before the steering edits).

## 3. The reader hands its findings over by hook (the spike)

A throwaway plugin with two identical agents (one with `omitClaudeMd: true`), a `SubagentStop` hook that dumps its payload and blocks a subagent's first stop once, run with `claude -p --include-hook-events`:

| Question | Result |
|---|---|
| Is `omitClaudeMd` honoured for a plugin agent? | yes: the agent with it answered `CLAUDEMD: NONE`, the other quoted the first ten words of the global `CLAUDE.md` |
| Does a `SubagentStop` entry in a skill's frontmatter fire? | **no**, in two runs no `SubagentStop` event occurred; in the plugin's `hooks/hooks.json` it fired (foreground and background) |
| What is in the payload? | `session_id` (the orchestrator's), `agent_id`, `agent_type` (`spike2:reader`), `agent_transcript_path`, `last_assistant_message` (raw: `<`, `>` and `&amp;` exactly as written), `stop_hook_active` |
| Does a matcher on the agent type work? | yes, the hook ran for `spike2:reader` and not for `spike2:plain` |
| Does `{"decision":"block","reason":...}` continue the subagent? | yes: its next reply started with the requested token, and the second stop had `stop_hook_active: true` |

Recorded as E18–E20 in `docs/what-is-true.md`. The plugin therefore ships `hooks/hooks.json` (matcher `agentic-maker:trace-reader`) and `omitClaudeMd: true` on the reader.

## 4. The ledger as the witness, watched

### 4.1 The state machine, with recorded input (no model spend)

A copy of `fixtures/skill-project`, the repo's sanitized stream as the baseline "worker", the real `ledger reader-done` handler fed a real-shaped payload:

```
D. edit SKILL.md, then ledger fix F1      ERROR conflict/edited_before_fix: ... changed after the newest recorded run and before `ledger fix` kept a copy of it
E. restore the bytes (new mtime), fix F1   ok            (content decides, not the clock)
F. ledger close --outcome clean            ERROR conflict/not_witnessed: ... 8 of 11 receipts fail in the newest take; ...#F1: no rerun-predicate verdict is recorded
                                           next: agentic-maker run release-notes --session lt2
G. rewrite the controlling text; check diff ok   -> phase rerunning
L-M. rerun (receipts 11/11), check predicate  [('F1', True)]  -> phase closing -> close clean accepted; F1 fixed
stale built binary                         ERROR conflict/stale_bin: the built binary .../bin/seeded-cli is older than the sources in the ledger's targets
the same F1 from two takes                 two ledger entries (...01/findings/1.json#F1 and ...02/findings/1.json#F1), two separate snapshots
reader hook, reply 1 (a fabricated quote)  {"decision": "block", "reason": "These findings did not verify against the trace:\nF1: quote does not appear verbatim ..."}
reader hook, reply 2 (in a code fence)     saved as 2.json, F1 verified, F2's rejection recorded; reader tokens 14 in / 1100 out (two records of one response counted once)
check findings with a trace.md label       "(Skill, ERROR) ...", "[18] assistant text: ...", "assistant text: ..." all verify with a note; an empty trace_refs and a fabricated quote are rejected
check predicate ^...$ regex                passes (matched per event, ^ and $ anchor lines); with --session only the findings being fixed are judged
```

### 4.2 Two whole loops under herdr (skill target `skills/manifest-synth`, a fresh interactive Claude orchestrator each, `--plugin-dir`, the user's bypass-permissions default)

| | Loop A (`--rounds 1`, $3) | Loop B (`--rounds 1`, $2, `/compact` while take 1 was running) |
|---|---|---|
| Orchestrator tool calls | **40** (Bash 22, Read 12, Agent 2, Glob 2, Edit 1, AskUserQuestion 1), **0 Write** | resumed after the compaction and finished |
| Round one's final loop (same kind of run) | 57 (Bash 31, Read 15, **Write 4**, Agent 2, SendMessage 1, ...) | |
| Receipts per take | 8/11, 9/11, **11/11** | 8/11, then 11/11 |
| Reader hand-over | both readers were sent back once by the hook and repaired their own quotes ("Stop hook feedback: These findings did not verify against the trace: F2: quote does not appear verbatim in the cited events [6]" ...) | same hook, no manual copy |
| User `CLAUDE.md` in the two readers' transcripts | **0 of 2** | |
| Reader tokens (in `ledger status`) | 26 in, 141,742 cache read, 28,535 cache create, 9,053 out | |
| Workers' cost | $0.123 of $3 | $0.064 of $2 |
| Close | `clean`, accepted after F1-F5 had a passing verdict from a take that ran after the fix (F4 by `ledger judge`, with its reason); findings `fixed` | **`open`**, honestly: the round limit stopped it with a P1 (the worker skipped the step-3 reread) and a P2 (the anchored script path) unfixed; findings `open` |

After the compaction, loop B read the finished take's output, spawned the reader, ran `ledger status`, then `ledger fix F1 F3 F4`, rewrote the skill, ran `check diff` for each finding and started take 2 without being told where it was. It also showed one flaw, fixed afterwards: it forgot `--run-id` for take 2, which landed in a separate run directory; `run --session` now keeps every take under the ledger's run.

### 4.3 Do pre-approved commands prompt? (E14)

A fresh interactive session in manual-permission mode, the skill invoked, then: `agentic-maker doctor --human` alone; `agentic-maker detect .` and `agentic-maker ledger status ...` as two parallel Bash calls; a `Read` and `agentic-maker doctor --human` in parallel; and the same command in a later turn after the skill's turn ended. **Seven calls, no approval dialog; the agent never went to `blocked`.** The "one Bash call per message" rule was removed from `derail`. The four prompts of round one stay unexplained.

## 5. Reading a session by id

`agentic-maker normalize session:<id>` and `run --runner existing --from session:<id> | herdr:<pane>` find a Claude, Codex or agy session. The Python adapters were compared with the `jq` recipes in `skills/derail/references/session-recipes.md`, event by event (kind and exact text or arguments), on one real session of each harness:

| Harness | File | Python events | jq events | Differences |
|---|---|---|---|---|
| Claude Code | the loop-B orchestrator transcript | 143 | 143 | 0 |
| Codex | a recorded worker run with 7 tool calls and 2 command results | 28 | 28 | 0 |
| agy | a recorded session with tool calls | 20 | 20 | 0 |

(Before the recipes and adapters were aligned there were three differences, all of them places where the adapter kept more than the recipe: non-text result blocks, `developer` messages, JSON spacing.)

- A herdr pane running agy resolves to `.../logs/transcript_full.jsonl` (not the 4096-character `transcript.jsonl`); a pane running Claude resolves to its `<session id>.jsonl`; an unknown id fails with `session_not_found` and a suggestion.
- A live Codex worker was started under herdr to run two commands. **It could not run**: the pane showed "Your access token could not be refreshed because you have since logged out or signed in to another account. Please sign in again." That is a step only the user can do, so the live Codex worker round was UNVERIFIED here; it was run after the release through `codex exec`, which could refresh its login (section 10). What the attempt did show: herdr 0.9.5 reports no `agent_session` for that Codex pane, and the resolver's fallback (read the id from the pane's status line, accept it only if a rollout of that id was recorded in the pane's directory) found the right rollout; its 8 events (including the harness's `developer` instructions) normalize.
- A reader can cite a Codex-derived trace: `claude -p --agent agentic-maker:trace-reader --restricted ...` over the 28-event Codex session returned valid JSON in 2 turns ($0.037); its finding cited events [14, 16, 18] and `check findings` verified it (1 verified, 0 rejected). This also shows the headless reader is a working fallback if the hook route ever fails.

## 6. A real skill, not planted: `convert-to-natural-writing`

The skill is one of the author's own (`skills-by-yigitkonur`), 1184 words plus six references and a script. It has `disable-model-invocation: true`, so a worker cannot choose it; only a slash command starts it. That case was not handled (A11): `scenario.py` now reads the skill's frontmatter, the dry-run says the prompt must begin with `/<wrapper>:<skill>` and that T1 cannot be observed, and `targets/skill.md` and `scenarios.md` carry a sentence about it. Without the slash the dry-run warns "a worker cannot choose it, so a run would never use it".

Two scenarios in Turkish on a scratch copy: a rewrite of a translationese paragraph (receipts: the version, date, percentage, command and link survive character for character, "yaklaşık" keeps its hedge, nothing invented, the source unchanged) and an audit (a findings file that quotes the text, the source unchanged). A fresh interactive orchestrator ran `/agentic-maker:derail skills/convert-to-natural-writing --rounds 1` ($4, 6 takes approved).

| | Result |
|---|---|
| Takes | rewrite 01, 02, 03: **11/11** receipts each; audit 01, 02: **6/6** each; five takes, $0.416 of $4 |
| What the skill does well (receipts and readers agree) | every protected literal survived in all three rewrites, nothing was invented, the audit quotes verbatim: the skill's invariants hold |
| Findings, not planted (readers: verified 4 of 4 and 2 of 2, none rejected) | the Rewrite row of the mode table says the deliverable is "backed by an internal invariant reconciliation pass", while section 3 calls the Active Ledger "mandatory"; the same contradiction in the completion checklist (F2, F3, P1). `scripts/audit-rewrite.py` is named nowhere in `SKILL.md` or the references, so a worker cannot discover it (F4, P2). In audit mode the Context & Genre field is stated once, not per entry, and the checklist mixes rewrite-only items into audit mode (audit, both P2) |
| The fix (two sentences, `check diff` accepted both, every `[NICE]` line intact) | see the diff below |
| Effect on the rerun | **none on the behaviour it aimed at**: in rewrite/02 and rewrite/03 the worker still goes Read, then Write and replies with a change summary, no Active Ledger. The orchestrator recorded F2 and F3 as failed (`ledger judge`, with its reasons, after reading event 8 of both takes) and **closed `open`**, not `clean` |
| Predicates | the two machine predicates could not judge fairly: one was an `order` of `Write` before `Write` (before at 6, after at 6), the other needed a ledger file the fix does not ask for. `check findings` now rejects an `order` predicate whose two calls are the same |
| Tooling quirk | both readers numbered their findings F1, F2; `ledger fix` refused the second reader's ids because the orchestrator passed the first take's trace. `--trace` now defaults to the one beside the `findings/` directory the file is in |
| Left to the skill's owner | whether a visible ledger in rewrite mode is wanted at all: all three rewrites were correct without one |

The edit, as a diff against the original (offered, not applied to the source repository):

```diff
--- /tmp/am-src/skills-by-yigitkonur/skills/convert-to-natural-writing/SKILL.md	2026-10-20 05:45:52
+++ /tmp/am-nw/skills/convert-to-natural-writing/SKILL.md	2026-10-21 03:43:24
@@ -31,7 +31,7 @@
 | Mode | Trigger Condition | Primary Deliverable |
 | :--- | :--- | :--- |
 | **Audit / Diagnose** | User asks why copy feels robotic, generic, translated, stiff, or AI-generated. | A structured Active Ledger identifying exact excerpts, structural flaws, reader harm, and natural alternatives. |
-| **Rewrite** | User requests humanizing, polishing, naturalizing, or rewriting draft content. | Clean, restructured deliverable backed by an internal invariant reconciliation pass. |
+| **Rewrite** | User requests humanizing, polishing, naturalizing, or rewriting draft content. | The rewritten text, saved where the user said. Write the Active Ledger (Phase 1) before the first rewrite and show it in your reply; create a ledger file only if the user asks for one. |
 | **Publication Review** | Draft is near-final and requires pre-publication verification. | Strict verification report detailing blockers, warnings, invariant checks, and release-ready text. |
 
 ---
@@ -107,7 +107,7 @@
 ## 6. Completion Checklist
 
 Before delivering output:
-- [ ] Active Ledger created with verbatim location, flaw, impact, and fix.
+- [ ] Active Ledger (verbatim location, flaw, impact, fix) was written before the rewrite began, and it is in your reply, or in the file the user named for an audit.
 - [ ] Every Exact, Value, Force, and Document invariant is strictly preserved.
 - [ ] Zero mechanical token blacklists or regex bans were applied.
 - [ ] No fake personal anecdotes or synthetic human quirks were fabricated.
```

## 7. Does the knowledge help? After the steering changes

### 7.1 Build tasks, with and without the plugin (the same three tasks as section 2)

Section 2's first numbers were confounded: the workers' compound commands (`cd ... && agentic-maker probe ... | head; ./seeded-cli ...`, `for` loops, heredocs) were denied by my narrow allow-list, so the plugin arm often could not run what it was told to run. All 27 runs below allow Bash (a user approving a build task would), had **0 permission denials**, and compare three arms: the plugin as it was before these steering edits (an exact copy of the previous commit), the plugin as it is now, and no plugin. Three samples each, graded by `agentic-maker probe` on what the worker left.

| Task | No plugin | Old plugin text | New plugin text |
|---|---|---|---|
| (a) `seeded-cli`: "agents keep tripping over it" (pristine: 11 findings, 4 High) | findings 4, 4, 4; High 2, 2, 2 | findings 2, 2, 2; High 1, 2, 1; skill fired 3/3; **probe run 0/3** | findings **0, 0, 0**; High **0**; skill fired 3/3; **probe run 3/3** |
| (b) build a small MCP server from `_mini.py` | findings 2, 0, 0 | findings 1, 0, 0; skill fired **0/3** | findings 0, 0, 0; skill fired **3/3**; probe run 3/3 |
| (c) clean up the 24-tool seeded MCP server (pristine: 16 findings, 2 High) | findings 4, 5, 4 (none High) | findings 0, 0, 0; skill fired 3/3; probe run 0/3 | findings 0, 0, 0; skill fired 3/3; probe run 3/3 |
| (d) add a tool that deletes a calendar event to a server that has `delete_user` | (section 2: all six runs copied the existing pattern) | skill fired **0/3** (section 2) | skill fired **3/3**; probe run 3/3; 0 findings; `delete_event` has `destructiveHint: true` |

- Reading it: the knowledge alone halves what the probe finds on the CLI task (4.0 to 2.0); telling the model to run the probe on what it built takes it to 0. The description now fires the skill on plain wording ("build an MCP server", "add a tool") where it fired 0 of 3 before.
- Caveats, stated plainly: the grader is the same probe the new-plugin workers were told to run, so 0 findings after they used it is expected; the old-plugin arm (knowledge without the probe instruction) is the arm that measures the knowledge. Three samples per cell. Small MCP servers come out clean without the plugin, so (b) and (d) show the trigger and the probe loop, not a quality gap.
- No gaming: all nine CLI results still have `list`, `get` and `delete`, valid JSON from `list --json`, exit 3 for a missing item, and a working `delete --yes`.
- Worker cost per cell (three runs): $0.20 without, $0.30 old, $0.39 new on (a); the probe loop costs about a third more.

### 7.2 `claude plugin eval` over `evals/` (10 cases, 3 runs each, with and without the plugin; $2.65, 195 s)

| Case | With | Without | Δ |
|---|---|---|---|
| ignores-chatbot-prompt | 1.00 | 1.00 | +0.00 |
| ignores-code-review | 1.00 | 1.00 | +0.00 |
| ignores-human-ui | 1.00 | 1.00 | +0.00 |
| ignores-react-form | 1.00 | 1.00 | +0.00 |
| ignores-rest-api | 1.00 | 1.00 | +0.00 |
| triggers-agent-interface-design | 1.00 | 0.00 | +1.00 |
| triggers-derailment-method | 1.00 | 0.00 | +1.00 |
| triggers-mcp-add-tool | 0.00 | 0.00 | +0.00 |
| triggers-mcp-build | 1.00 | 0.00 | +1.00 |
| triggers-skill-write | 1.00 | 0.00 | +1.00 |

Mean Δ +0.40. The five stay-quiet cases (three new: a REST API for a web frontend, a chatbot system prompt, a React form) score 1.00 with and without the plugin. Of the new trigger cases written in plain words (no "agent" in the prompt), "build me a small MCP server" and "write a SKILL.md for our deploy process" fire the skill every time. "Add a tool to our MCP server that deletes a calendar event" scored 0: the sandbox has no such server, the model searched for it (`Grep` for `McpServer|FastMCP|registerTool`) and never reached the skill. The case was rewritten to be self-contained (the three existing tools are named in the prompt) and rerun: 1 of 3 fire (Δ +0.33). A small, direct design question is answered without the skill; the same request as work on real code fires it 3 of 3 (7.1, row d).

### 7.3 In a normal session with every skill installed

`claude -p "Build me a tiny command-line tool called todo that lists the tasks in tasks.txt and marks one done, so that our automation agents can use it. Put it in this folder."` with `--plugin-dir` and no restriction, on the author's machine (**104 skills installed**, among them the three `audit-*` skills this plugin replaces), two runs: `agentic-maker:agent-interface-design` was called in both, and each run ran `agentic-maker probe` on the tool it had built once (25 and 19 tool calls, $0.25 and $0.22).

## 8. The audit and the knowledge pages

- `agentic-maker probe cli|mcp` saves its whole reply under `.agentic-maker/runs/audit-<date>/probe-*.json` (ignored by git) and prints the path as `evidence_file`; the MCP envelope stays compact while the file holds the per-tool rows. The audit cites the file; the line "the target must not be run again by hand" is replaced by "read that file or rerun the same probe".
- The first audit of the clean twin (section 1.3) put `delete 1 --dry-run` into `--safe`, against the skill's rule, and said so. The rule gave the prohibition without the reason; it now says why (whether the dry-run flag is honoured is part of what is being audited, and a CLI that ignores it runs the command), and the same sentence is in `agent-interface-design`.
- `agent-interface-design/SKILL.md`: a description in the words people use, a "Check what you built" section (run the probe, fix, run again), a "When an agent already misbehaved" section (read the session by id), a row for tools that delete or send, and two blocks generated by `scripts/build-index.py` (which index page lists each stack's pages; every index), checked by `--check`. The probe instruction is also in `contract.md`, `cli/checks.md` (finish criteria) and `mcp/hard-rules.md` (rule 15).
- `design` asks the interview of the chosen surface (`interview-mcp.md`, new `interview-cli.md` and `interview-skill.md`). Run under herdr with the author as the user: a CLI idea (list and cancel scheduled database backups) got "Who runs it" and "Distribution" as dialogs, the open questions as plain text, then group 2 (output, credentials, destructive operations), with no MCP question; an MCP idea (wiki search with per-user permissions) got the surface choice with labelled evidence and "group 1 of 3" of the MCP interview.

## 9. The whole ledger once more, on the 0.2.0 text

Run after the last text change (`dd0844a`; `9a80f0f` changed only versions and docs).

| Row | What ran | What it showed |
|---|---|---|
| Static | `scripts/check.sh --strict-parity`, `claude plugin validate . --strict` | `lint-refs: 328 files, 0 violations`, `check-links: 578 links + 148 backticked paths, 0 broken`, `build-index: 0 stale`, `plugin agentic-maker 0.2.0 / marketplace 0.2.0 / code 0.2.0`, `always-on: 323 tok`, `UNMAPPED: 0`, `ALL CHECKS PASSED`; `Validation passed` |
| Clean twin | `claude -p "/agentic-maker:audit clean-cli/clean-cli"` (restricted, Bash only for `agentic-maker *`) | 7 tool calls, $0.092, 0 permission denials, first call `agentic-maker probe cli clean-cli/clean-cli`, sentinel absent. Overall 100 (4 of 8 dimensions measured), no Critical or High finding, three Low observations (the help examples lack `schema_version`; the probe shows only the head of a long `suggestion`; `--token-file`, `--no-input`, `--timeout` are barely documented and no exit code is listed for an auth failure). The report names both replies, saved under `.agentic-maker/runs/audit-20261021/` as `probe-cli-041605.json` and `probe-cli-041610.json` |
| Ledger as witness | the four recorded walks (no model): close clean before a rerun, edit before `ledger fix`, stale binary, two takes' F1 | `ERROR conflict/not_witnessed: ... 8 of 11 receipts fail in the newest take; ...#F1: no rerun-predicate verdict is recorded`; `ERROR conflict/edited_before_fix`; restore, fix accepted; `ERROR conflict/stale_bin`; findings keys `.../01/findings/1.json#F1` and `.../02/findings/1.json#F1`; after a rerun at 11/11 and a predicate verdict, `ledger: closed clean` |
| Sessions by id | adapters against the jq recipes on a real Claude, Codex and agy session | `claude python 143 events \| jq 143 \| only-in-python 0 \| only-in-jq 0`, `codex 28/28/0/0`, `agy 20/20/0/0` |
| Whole loop, interactive | a fresh Claude orchestrator under herdr (`--plugin-dir`, the user's bypass-permissions default), `/agentic-maker:derail skills/manifest-synth --rounds 1` on a copy of `fixtures/skill-project`, on the commit after `dd0844a` | 3 takes with receipts **8/11, 11/11, 11/11**; 3 readers, each hand-over by the hook (`reads`: verified F1-F5, F1, none; none rejected), user `CLAUDE.md` in the readers: **0 of 3**; reader tokens recorded per read; **0 `Write`** by the orchestrator; 54 distinct tool calls (44 without task bookkeeping; Bash 26, Read 11, Agent 3, Edit 2) against 40 for loop A in section 4.2, which had 2 readers; workers $0.099 of $3. It fixed F1 (trigger text), F4 (wrong path), judged F5 failed on both post-fix takes with `ledger judge --fail` and a reason, and closed **`open`** at the round limit: `status closed, outcome open, rounds 1/1`, findings left `open`. The readers disagreed with the orchestrator on F5 (P2 / acceptable) and it said so in its report |
| Reader hand-over | a headless orchestrator (`--session-id` = the ledger's id) spawns the real `agentic-maker:trace-reader` on a recorded take | the hook sent the reader back once (`F1: belief_source=observed but no cited event carries thinking text; use inferred`, `F3`, `F4: quote does not appear verbatim`), the repaired reply is `2.json` with `2.verified.json` = F1..F6, `reader_tokens` 10 in / 5,881 out / 57,407 cache read / 14,363 cache create, `phase fixing`, user `CLAUDE.md` in the reader transcript: 0, $0.155, 0 denials |

One row failed the first time and passed on the one rerun, for a reason in the setup and not in the code: the first run created the ledger as `--session fh1` while the headless orchestrator had its own session id, so the hook (which finds the ledger by the payload's `session_id`) found no ledger and did nothing, exit 0, no file. The skill always passes `${CLAUDE_SESSION_ID}`, which is the id the hook sees; the rerun used the orchestrator's real id. A hand-run loop that names its ledger anything else gets no hand-over and `ledger status` stays at `reading`.

Not rerun: the real-skill loop (section 6; `b424e9b`), the build tasks and the eval cases (section 7) and the two `design` interviews (section 8). Since the two interactive loops, code changed in `check.py` (the `--trace` default, an `order` predicate with identical calls is refused), `scenario.py` (user-only skills), `sessions.py`, `trace.py` and `cli.py` (probes keep their reply). The recorded walks, the live reader and the interactive loop above cover the loop's own path through those files. What stays unrerun is the real-skill loop (section 6), the build tasks and evals (section 7) and the design interviews (section 8).

## 10. After the release: install, a live Codex worker, the third-party samples

Run on 0.2.0 as published (`667dcd7`) and on the 0.2.1 branch.

| Row | What ran | What it showed |
|---|---|---|
| Install, one line | `claude plugin install agentic-maker --marketplace yigitkonur/plugin-agentic-maker` in an empty `CLAUDE_CONFIG_DIR` | `Successfully added marketplace: plugin-agentic-maker`, `Successfully installed plugin: agentic-maker@plugin-agentic-maker (scope: user)`; `claude plugin list`: 0.2.0, enabled; `claude plugin details`: always-on ~323 tok, `SubagentStop (harness-only — no model context cost)`; `marketplace update`, `update` (`already at the latest version`), `uninstall` all succeed |
| Install without an ssh key | the same with `SSH_AUTH_SOCK` unset and `GIT_SSH_COMMAND` given an empty identity (`Permission denied (publickey)`) | `SSH clone failed, retrying with HTTPS: https://github.com/yigitkonur/plugin-agentic-maker.git`, then installed; an anonymous `git ls-remote` over https (no credential helper) lists `HEAD` and `v0.2.0` |
| Install in the app | `/plugin marketplace add yigitkonur/plugin-agentic-maker`, `/plugin install agentic-maker@plugin-agentic-maker` in an interactive session under herdr (scope picker: user) | `Successfully added marketplace`, `✓ Installed agentic-maker. Plugin is now active.`; afterwards uninstalled and the marketplace removed, `claude plugin list` shows no `agentic-maker@` |
| Audit from that session | `/agentic-maker:audit clean-cli/clean-cli` in the same session (the user's normal setup, all skills) | the fork ran `agentic-maker probe cli` four times with its own `--safe` sets, overall 85, F1 High: `get 1 2 --json` returns item 1 with `ok:true` (the probe: two Medium `exit_codes` findings on `list extra` and `get 1 2`), F2-F6 Medium and Low documentation gaps; one probe expectation (`get abc --json # expect-exit 6`) was the audit's own mistake and it said so. The main session reran the F1 commands itself and they matched |
| Clean twin, fixed | the twin rejects extra positional arguments and `delete` of a missing item; help examples and exit codes match the code | before the fix, `probe cli` with `--safe "list extra --json # expect-exit 2" --safe "get 1 2 --json # expect-exit 2"`: 2 Medium; after it: 0, and 0 for the default probe and for each of the audits' probe sets |
| Live Codex worker | `codex exec --sandbox workspace-write` (codex-cli 0.163.0) on the `cli-items` scenario in a scratch folder | `report.json` written (item 7 reported missing), sentinel absent. `run cli-items --runner existing --from session:<id>` resolved `harness: codex` and the rollout path, receipts **3/3**; the trace has 29 events and 5 tool calls with Codex's exit codes (`ERROR exit=1` on `get 7`). The real reader (headless orchestrator, ledger keyed by its session id) was sent back once by the hook (`F1: trace_refs [30] do not exist in the trace`) and its repaired F1 verified: the worker merged `get`'s bare `{"id": 2}` with the name from `list`, controlling text `get <id>          show one item` (a planted defect). The worker also read `~/.codex/memories/MEMORY.md`: a Codex worker is not a clean room |
| Codex pane by herdr | `normalize herdr:<pane>` on an interactive Codex pane | herdr reported no session; the id was taken from the status line and matched the rollout recorded in that pane's folder (warning says so). The interactive Codex in that pane could not refresh its login (`Your access token could not be refreshed ...`) on two starts, while `codex exec` could |
| Third-party TypeScript | the 98 blocks re-extracted from the current pages and type-checked with the missing packages installed (`npm install --ignore-scripts`; `openai` 7.39.0, `langchain` 1.5.18, `@langchain/classic` 1.0.54, `prom-client` 15.1.3, `ioredis` 6.0.0, `@opentelemetry/*` 2.12.0, `vitest` 5.0.5, `commander` 15.0.0 and 15 more) | three page defects, fixed: `langchain/agents` does not exist (`TS2307`; the agents moved to `@langchain/classic/agents`), `toolCall.function` needs `toolCall.type === 'function'` first (`TS2339`; `openai` 7 has custom tool calls), `prom-client` is deprecated ("replaced by @prometheus-io/client"). Afterwards no npm import fails to resolve; the 306 errors left are names a sample takes from another page (269 `TS2304`), two user JSON files, `cloudflare:workers` without the Workers type setup, and default imports of `ioredis`/`ajv` under `nodenext` ESM. `@opentelemetry/sdk-trace-node` 2.x is deprecated in favour of `@opentelemetry/sdk-trace` 3.0, which has no drop-in `NodeTracerProvider`; that sample is left as it is |

## 11. Releases and updates by themselves, `build-skill` brought in, a second real skill

Run on `main` after 0.2.1 (Claude Code 2.1.307, herdr 0.9.5).

| Row | What ran | What it showed |
|---|---|---|
| Release decision | `scripts/release.py` in fresh clones, one commit kind each | docs only → none; unprefixed change to `lib/` → patch; unprefixed README tweak → none; `fix` → patch 0.2.2; `feat` → minor 0.3.0; `refactor!:` and `BREAKING CHANGE` at 0.x → minor; a `chore(release)` commit is ignored; an empty `## Unreleased` section is dropped and the notes generated from the commits; a tag that already exists is refused |
| Release workflow, no release | PR #4 merged (`ci:` and docs commits only) | run `release` on `20dea21`: `"current": "0.2.1", "level": "none", "release": false`, success, no tag |
| Release workflow, a release | PR #5 merged (`feat(skills): /agentic-maker:build-skill ...`) | within 100 s, with nobody touching it: commit `chore(release): v0.3.0` by `github-actions[bot]`, tag `v0.3.0`, GitHub release `agentic-maker 0.3.0` as Latest, version 0.3.0 in `plugin.json`, both `marketplace.json` fields and `__version__`, a generated `## 0.3.0` changelog section. The Codex review of PR #4 found four real problems in the workflow before it ever ran (a manual run on a feature branch could push it to `main`; a rebase after the gate; success reported when every push failed; an empty Unreleased section crashed the script), and a fifth was found while fixing them (a queued run checked out its own older commit and could reuse a released version); all five are fixed |
| Auto-update | a scratch project in the real config: project scope, **disabled**, `autoUpdate: true` on the marketplace entry, 0.2.1 installed; an ordinary interactive session, first message sent; no `update` command | **285 s later `installed_plugins.json` said 0.3.0** for that project. The 14 other project installs stayed at 0.2.1: the check runs for the project a session is started in, so each one updates when it is next used; they were brought to 0.3.0 with `claude plugin update ... --scope project`, all 15 `Scope: project`, none enabled. What the docs say and this confirms: the switch is `autoUpdate` on the marketplace entry (off by default for third-party marketplaces), the trigger is a changed `version` string, the check runs after the first message, the new version loads on the next start |
| Other plugin repos | survey of the seven others under `~/plugins` | five (mcp-use, sentry, testsprite, trigger-dev, typescript-optimizer) already carried their own release automation, so none was added; `plugin-cf-browser` had a live session editing it; `plugin-kernel-sh` ships two plugins with independent versions, which a one-version script does not model. No change made to any of them |
| `build-skill` | the author's `build-skill` read in full, 12 pages re-cut by 12 writer agents and audited by 12 second agents (24 agents, 222 tool calls) | the auditors removed or softened claims they could not confirm against the Claude Code docs or the CLI (for example an invented description limit, a wrong claim that `claude plugin validate` flags unknown frontmatter keys, a `grep` that missed `when_to_use:`); I checked the `eval-emit`, `claude plugin eval` and `scan` commands the test page cites against `--help`. Left out on purpose: the Node download scripts, registry publishing, the generic research pages |
| Derail on a second real skill | `/agentic-maker:derail skills/build-skill --rounds 1` on a scratch copy of the author's `build-skill` (user-only skill, so the scenario prompt starts `/target:build-skill`), scenario: make a skill for an internal CLI from a local doc | 2 takes, receipts **11/11 and 11/11**, $0.22 of $4; reader findings 5 verified, 0 rejected, no user `CLAUDE.md` in the reader (0 of 1). The worker passed every receipt while skipping the skill's own gates: it said it skipped the mandatory research step (F1: the skill says to refuse without the `research` plugin or internet), added advice that is not in the source doc (F2), pointed validation at `scripts/validate-skills.py`, which does not exist (F3), and never applied the shipping checklist because it is written about `build-skill` itself (F4). Rewriting the text closed F1-F3 on the rerun (F2 and F3 by `ledger judge`, after the automatic predicates tested the wrong event); F4 failed its rerun (the worker never opened the checklist) and the loop closed **`open`** at the round limit |
| The plugin's own `build-skill`, run once | `run make-skill-plugin` (kind plugin, prompt `/agentic-maker:build-skill ...`, the same task and the same 11 receipts), headless, restricted | receipts **11/11**, $0.059, 4 tool calls, the 45-line `skills/acme-report/SKILL.md` it wrote traces to the doc (commands, exit codes, the 400-day cap, the semicolon gotcha). It did **not** show the skill's procedure being followed: no `claude plugin validate`, no checklist, a first compound Bash call was denied and not retried, and it ended "I haven't tested it". The stream does not show whether the slash command's body reached it. One sample: the claim that the procedure steers a worker is **UNVERIFIED**; the next check is `/agentic-maker:derail` on this skill with scenarios whose receipts need the validate step |

The edit to the author's skill, offered and not applied to their repository:

```diff
--- skills-by-yigitkonur/skills/build-skill/SKILL.md	2026-10-25 18:52:11
+++ skills/build-skill/SKILL.md (after the loop)	2026-10-25 19:10:28
@@ -19,7 +19,11 @@
 - **Install command**: `claude plugin marketplace add yigitkonur/plugin-research-powerpack`, then `claude plugin install research@plugin-research-powerpack`
 - **Skills it provides**: `/research:ask` for one question, `/research:deep` for a multi-source run that ends in files, `/research:verify` to fact-check a document
 
-> **Standing Invariant**: Never draft a skill based on assumptions, unverified library contracts, or generic training weights. When non-trivial APIs, frameworks, or domain workflows are involved, run `/research:ask` (on
+> **Standing Invariant**: Never draft a skill based on assumptions, unverified library contracts, or generic training weights. Every skill needs a ground-truth source, which is one of:
+> 1. **A source the user supplied** (a local doc, a file path, pasted text). Read it in full. It is your ground truth, and no research plugin or internet is needed.
+> 2. **Web evidence** gathered with `/research:ask` (one question) or `/research:deep` (five or more sources or entities), with cited, verbatim quotes. If the `research` plugin is not installed, prompt the user to insta
+>
+> If you have neither a user-supplied source nor web access, ask the user for a source before drafting. Quality skills cannot exist without quality context.
 
 ## When to Use
 
@@ -39,7 +43,7 @@
 ## Core Non-Negotiable Rules
 
 1. **Specification compliance first**: Frontmatter strictly adheres to `agentskills.io/specification` (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`). No arbitrary top-level fields.
-2. **Context grounding before drafting**: Run `/research:ask` or `/research:deep` for all non-trivial domains. Refuse to run without verified research and refuse to hallucinate APIs or edge cases.
+2. **Context grounding before drafting**: Ground the skill in a user-supplied source or in `/research:ask` / `/research:deep` evidence (see the Standing Invariant). Every factual claim in the new skill must trace to a l
 3. **Progressive disclosure architecture**: Keep `SKILL.md` under 500 lines (<5,000 tokens). Offload bulky documentation to `references/` (1-level deep) and deterministic operations to `scripts/`.
 4. **Deterministic scripting**: Write bundled scripts in portable JavaScript (`.mjs` ES Modules) or Python (`.py`). Avoid fragile shell scripts (`.sh`).
 5. **Reproduce, test, and verify**: Always test scripts and verify execution infrastructure before declaring done.
@@ -103,9 +107,9 @@
 
 ## Step-by-Step Authoring Workflow
 
-1. **Verify Prerequisites**: Confirm the `research` plugin (or an equivalent web research tool) is available and `node scripts/skill-dl.mjs --where` succeeds.
+1. **Verify Prerequisites**: Identify the ground-truth source (a user-supplied doc, or the `research` plugin / an equivalent web research tool). `<build-skill-dir>` below means the directory containing this SKILL.md; ru
 2. **Select Mode**: Choose Discovery, Creation, Conversation-driven, or Documentation mode.
-3. **Execute Research**: Collect evidence via `/research:deep` (or `/research:ask`) and `skill-dl.mjs search`. Build the comparison table.
+3. **Execute Research**: If the user supplied a source, read it in full and skip web research. Otherwise collect evidence via `/research:deep` (or `/research:ask`) and `skill-dl.mjs search`, and build the comparison tab
 4. **Draft `SKILL.md`**:
    - Write valid YAML frontmatter conforming to `agentskills.io`.
    - Formulate clear imperative workflow sections with validation gates.
@@ -114,8 +118,9 @@
    - Author automation scripts in `scripts/` using Node.js (`.mjs`) or Python (`.py`).
    - Run and test scripts with real data; confirm zero-crash execution.
 6. **Spec & Quality Validation**:
-   - Run `node scripts/skill-dl.mjs inspect .` to verify frontmatter and line counts.
-   - Run repository skill validator: `python3 scripts/validate-skills.py`.
+   - Run `node <build-skill-dir>/scripts/skill-dl.mjs inspect <new-skill-dir>` to verify frontmatter and line counts.
+   - If node or the command is unavailable, check by hand: `name` equals the directory name, `description` is under 1024 characters with no `<` or `>`, `SKILL.md` has fewer than 500 lines, and every file routed from `SK
+   - Read [`references/checklists/master-checklist.md`](references/checklists/master-checklist.md) and tick it against the new skill.
 
 ## Do This, Not That
 
@@ -169,12 +174,13 @@
 
 ## Final Shipping Verification Checklist
 
-- [ ] Frontmatter strictly contains valid `agentskills.io` fields (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`)
-- [ ] `name` matches directory name exactly (`build-skill`)
-- [ ] Description states WHAT the skill does and WHEN to use it (<1024 characters, no `<` or `>`)
-- [ ] `SKILL.md` line count is under 500 lines
-- [ ] Research prerequisite (the `research` plugin) is documented with its install command
-- [ ] All bundled scripts in `scripts/` are written in Node.js (`.mjs`) or Python (`.py`)
-- [ ] Bundled scripts execute cleanly (`node scripts/skill-dl.mjs --where`)
-- [ ] Every file in `references/` is explicitly routed in the reference routing section
-- [ ] Full repository validation passes: `python3 scripts/validate-skills.py`
+Apply every item to the NEW skill you built, not to this skill:
+
+- [ ] The new skill's frontmatter strictly contains valid `agentskills.io` fields (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`)
+- [ ] The new skill's `name` matches its directory name exactly
+- [ ] Its description states WHAT the skill does and WHEN to use it (<1024 characters, no `<` or `>`)
+- [ ] Its `SKILL.md` line count is under 500 lines
+- [ ] Every command, path, flag and fact in it was checked against the ground-truth source; nothing is invented
+- [ ] Any bundled scripts are written in Node.js (`.mjs`) or Python (`.py`) and were run once
+- [ ] Every file in its `references/` is routed from its `SKILL.md`, and every routed file exists
+- [ ] The validation step above was run (or done by hand) and its result reported
```
