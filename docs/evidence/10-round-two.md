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

Still not checked: 22 third-party packages that were not installed (`openai`, `pino`, `ioredis`, `@langchain/*`, `@opentelemetry/*`, `vitest`, `@aws-sdk/client-sqs`, `@vercel/blob`, `commander`, ...): those samples are checked for syntax only. Three blocks fail for reasons that belong to the compile setup, not to the page (`Ajv` default import under `nodenext`, a Cloudflare `Message` type that shadows a placeholder, relative imports without a file extension).

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

The same tasks are rerun after the steering text changes (last section).

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
- A live Codex worker was started under herdr to run two commands. **It could not run**: the pane showed "Your access token could not be refreshed because you have since logged out or signed in to another account. Please sign in again." That is a step only the user can do, so the live Codex worker round is UNVERIFIED. What the attempt did show: herdr 0.9.5 reports no `agent_session` for that Codex pane, and the resolver's fallback (read the id from the pane's status line, accept it only if a rollout of that id was recorded in the pane's directory) found the right rollout; its 8 events (including the harness's `developer` instructions) normalize.
- A reader can cite a Codex-derived trace: `claude -p --agent agentic-maker:trace-reader --restricted ...` over the 28-event Codex session returned valid JSON in 2 turns ($0.037); its finding cited events [14, 16, 18] and `check findings` verified it (1 verified, 0 rejected). This also shows the headless reader is a working fallback if the hook route ever fails.
