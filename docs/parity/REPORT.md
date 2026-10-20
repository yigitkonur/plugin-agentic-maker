# Parity report: what the plugin carries of the three skills it replaces

Recorded 2026-10-20. The three source skills are `audit-agentic-cli`, `audit-agentic-mcp` and `audit-skill-by-derailment` from `yigitkonur/skills-by-yigitkonur`. The numbers below are produced by `scripts/parity.py` (run `AM_SRC=<dir holding the three skills> scripts/check.sh --strict-parity`) and by the fixture runs listed in `docs/evidence/`. Nothing here is a claim from memory.

## 1. Every heading is accounted for

| | Count |
|---|---|
| Source headings (H1-H3, outside code fences) in `SKILL.md`, references and script docs | 948 |
| Claimed by a `<!-- src: ... -->` provenance marker in the new files | 904 |
| Dropped on purpose, each with a reason in `dropped.*.tsv` | 44 |
| Unmapped | **0** |
| Markers that name a heading which does not exist | **0** |

The 44 dropped headings are all navigation, not content: tables of contents and "Contents" lists (the files are split, so every section they listed is itself mapped), source-file routing tables keyed to file names that no longer exist, three document titles, one empty heading, and one user-level policy ("Delegation policy"), which belongs in a user's own settings and not in a reference about MCP servers. The full list with reasons: `dropped.A1.tsv`, `dropped.A2.tsv`, `dropped.B.tsv`, `dropped.C.tsv`, `dropped.D.tsv`.

The 11 non-markdown files (3 `openai.yaml`, 8 scripts) are in `files.tsv`, each with its replacement:

| Source | Now |
|---|---|
| `openai.yaml` (no implicit invocation), three of them | `disable-model-invocation: true` in the frontmatter of `audit`, `design`, `derail` |
| `audit-cli-help.sh`, `diff-cli-help.sh` | `agentic-maker probe cli`, `probe cli-diff` |
| `audit-mcp-server.sh`, `measure-context-budget.sh` | `agentic-maker scan mcp` (locates), `probe mcp` (runs `tools/list`, measures) |
| `launch-derailment.sh`, `parse-derailment-trace.sh` | `agentic-maker run`, `normalize` |
| `audit-worker-pane.sh`, `read-herdr-panes.sh` | `check receipts`, `normalize`, `skills/derail/references/runners/herdr.md` |

## 2. Table keys and tokens: soft check, triaged

The soft check looks for every table row key and every backticked token or threshold of the sources in the new corpus. 129 were not found verbatim. Each has a row in `accounted.tsv` with the reason; `scripts/parity.py check --soft --strict-soft` fails while any item has no row (currently 0). By kind:

| Why it is not found verbatim | Rows | Example |
|---|---|---|
| Carried in another form (a table split into cells, a short flag written as two cells, a marker inside a code block, a number written with a comma) | 27 | `-j, --json`; the Pare token benchmarks (`382 tokens` is now a number cell next to a unit) |
| Navigation: links, source-tree paths, routing-table labels | 35 | `../patterns/security.md`; the row labels of the old reference-routing table |
| Replaced script, placeholder of a replaced mechanism, harness-specific name, install path | 25 | `scripts/audit-cli-help.sh`; `$COORDINATOR_PANE_ID` (the worker now reports through files); `invoke_subagent` |
| Author-local: recorded pane ids, project names in a case table (listed by hash in `accounted.tsv`), companion skills | 32 | `w2N:pP`, a project name from a recorded case table, `linear-cli` |
| Domain leak of the video-flow skill | 7 | `.mp4`, `__TAKE_RESULT_JSON_START__` |
| A source repository cited as evidence; the claim is kept, the link is not | 3 | `GLips/Figma-Context-MCP` |

Triage found no lost behaviour. It did confirm by grep that the numbers and thresholds that carry advice (`2000 tokens`, stage budgets, the compaction table, `--description-chars`, `--schema-chars`, `--response-chars`, `--tool-threshold` with their defaults) are in the new files or in the CLI's options.

## 3. What changed shape on purpose

Each of these is a decision, recorded in `docs/design/` and checked against a real Claude Code in `docs/what-is-true.md`.

| Source behaviour | Now | Why |
|---|---|---|
| Worker is told where the skill is ("There's a skill for this at X") | The prompt is an everyday request that never names the target | The old prompt bypassed the layer where most skill failures start: whether the skill is chosen at all. New taxonomy codes T1-T3 cover it |
| Worker annotates its own run with `[STUCK]`/`[GUESSED]` | The read-only reader assigns the markers from the trace; self-annotation is an optional flag with its bias documented | Self-report is biased and changes the behaviour it describes |
| "Find 20-30 friction points" | Search by dimension; "none found in this dimension" is a valid answer | A quota invites invented findings |
| Toggle `Ctrl+O`, read the scrollback | Structured record first (`stream-json`, session transcript, Codex rollout), scrollback only as a fallback | A folded view hides what the agent did. Observed in a live herdr round: `Ctrl+O` in Claude Code toggles a transcript view |
| Worker calls back through `herdr agent prompt <coordinator pane>` | The worker writes files; the coordinator waits in the background | herdr-conductor forbids prompting the caller's own pane and forbids polling |
| Mode A: cheap in-session run | Dropped. `run --runner headless --max-turns 8` is the cheap smoke run | An in-session subagent inherits the parent's skills and CLAUDE.md, so it is not a fresh session |
| 21 root-cause codes | The same 21 with frozen ids, plus T1-T3, M7, O7, O8, C5 | Skills fail at the trigger; CLIs and MCP tools fail in ways the 21 did not name |
| Scripts documented by sidecar `.sh.md` files | `agentic-maker <command> --help` carries examples and exit codes | The plugin's own audit demands it of others |
| Exit codes 0-7 in one file, 0-8 in another; batch "partial" as 3 | One table, 0-8, partial = 8 | Inherited defects 1-2 (`docs/design/appendix-b-inherited-defects.md`) |

Reconciled inherited defects (25 listed in the appendix) were fixed during migration, not copied. Two additions by the migration subagents were checked in the second review (`docs/evidence/09-second-review.md`): the CIMD/DCR detection field names match the 2025-11-25 authorization spec, and the "polling-tool" pointer resolves. The registration order around them was wrong and is corrected.

## 4. Behavioural parity on the seeded fixtures

Fixtures are small, written by the same hand as the probes, and live in `fixtures/`. They show the checks work and are safe; they are not a recall rate on real-world tools.

| Fixture | Planted defects | Plugin | Old scripts | Clean twin |
|---|---|---|---|---|
| bash CLI (`fixtures/cli/seeded-cli`) | 11 | **10 found directly, 1 through its cause** | 4 directly, 1 more as a missing standard flag; all text-level | 0 findings, exit 0 |
| stdio MCP server (`fixtures/mcp/seeded-server.py`) | 11 groups, 24 tools | all groups found, 18 findings today (17 when first recorded); budget 5724 chars / 24 tools equals a `jq` hand count | counted 15 tool candidates, ~459 tok, flagged nothing | 0 findings |
| skill (`fixtures/skill-project`) | jargon description, opaque name, relative script path, typo in a reference path, a threshold without a number | 4 verified findings in run 1 (1 rejected); the run-2 reader found the untriggered skill (T1) | not runnable: the old modes name the skill | n/a |

No finding that failed `check findings` was ever accepted: the reader's quotes are verified verbatim against the trace before any edit (2 of 8 reader findings were rejected in the two skill runs; see `docs/evidence/04-derail-loop.md`).

Tables per defect: `docs/evidence/05-audit-cli.md`, `06-audit-mcp.md`.

## 5. Derailment parity

- A known derailment the old skill would also catch: the relative script path (S3) and the reference path typo are found in run 1 of `04-derail-loop.md`, fixed by rewriting the controlling text, and gone in the rerun.
- A derailment the old modes could not catch: run 2 of the same experiment ended with the skill never triggered (T1). Its description is rewritten and the predicate `tool_used: Skill` turns true on both reruns.
- The Stop gate refuses "Fixed." after an edit with no fresh run (`04-derail-loop.md`, "The Stop gate in the real harness").
- A live herdr round with a Claude worker: 11 of 11 receipts, `Ctrl+O` observed (`07-live-herdr.md`).

## 6. Not carried or not proven (read before deleting anything)

| Item | State |
|---|---|
| Live Codex and agy workers | Not run. The Codex rollout parser is built from real rollout files; agy is never launched (a launch can have effects the plugin cannot see, such as which account or quota it uses) |
| `Ctrl+O` behaviour in Codex and agy | Not observed |
| Authenticated MCP servers (OAuth) | Not measured; reported as such and routed to `mcpc` or the MCP Inspector |
| The `design` interview | The skill loads and routes; the 12-question interview is interactive and was not run end to end |
| `--bare`, `claude --bg` | Not used; `--bare` cannot be the clean room (API key only, no skill listing) |
| Dated MCP facts (client matrices, model behaviour, platform prices, CVEs) | Carried into `references/fresh/` with their dates; none was re-verified for this release |

## 7. Checklist for deleting the three original skills

Deleting them is the repository owner's decision. Every item below can be re-run.

- [ ] `AM_SRC=<clone of skills-by-yigitkonur>/skills scripts/check.sh --strict-parity` passes: 948 headings, 0 unmapped, 0 dangling.
- [ ] `python3 scripts/parity.py check --no-write --soft --strict-soft` reports 0 unaccounted table keys and tokens.
- [ ] Read `accounted.tsv` rows with "author-local" and "domain leak" reasons and agree they should not be carried.
- [x] Read the two migration-subagent additions named in section 3 (done in the second review).
- [ ] Install the plugin from GitHub in a clean config and run `/agentic-maker:audit` on one of your own CLIs and one MCP server you know the faults of.
- [ ] Tag the source repository before deleting (git history is the archive).
