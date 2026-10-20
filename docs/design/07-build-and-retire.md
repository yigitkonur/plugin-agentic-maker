> Part of the `agentic-maker` plan · [README](README.md)

## 11. Build order and the gate for deleting the originals

Smallest thing that runs first. The **v1 `agentic-maker` CLI is five commands** — `doctor`, `run` (claude `stream-json` only), `normalize` (claude only), `check` (`receipts|findings|diff|nice`), `ledger` — python3 stdlib. Everything else is deferred until a milestone needs it: `detect`/`surfaces.tsv`, `scan`, `probe cli`, `probe mcp` (a stdlib JSON-RPC/HTTP/OAuth client is real work), `cli-diff`, `collect`, `eval-emit`, codex/agy adapters, the herdr runner, the `Workflow`, a `setup` skill, the `fresh/` staleness check.

**M0 — spike, no plugin (1–2 sittings).** Resolve §12 with real runs on one skill (U1–U14). Output: a one-page "what's true" that edits this plan before any code.
**M1 — derail a *skill*.** `derailment-method`, `trace-reader` (Read/Grep/Glob), `derail` with runners **`existing`** (no launch; best value per cost — reads a session you already have) and **`headless`** (claude); the 5-command CLI; the `check` gates; H2 with kill switch. **Dogfood: derail the plugin's own two knowledge skills.** If loop state is lost on compaction → H3; if the orchestrator skips `check` → H1.
**M2 — derail & audit a *CLI*.** Cold `--help`-only scenarios; `probe cli` (+ `cli-diff`); `agent-interface-design` with the CLI references migrated (Appendix B fixes), `audit` (CLI path), `frameworks/` for the stacks in the three-project test; `surfaces.tsv` + `detect`.
**M3 — live & multi-harness.** herdr runner (conductor rules, `approvals:`), codex/agy adapters, `eval` runner if U13 passes, harness observation notes.
**M4 — MCP.** `probe mcp` (stdio + unauthenticated Streamable HTTP; `mcpc`/Inspector routing), `scan mcp`, MCP references (+`fresh/`), `design` command, decisions, iterative repair, interview.
**M5 — hardening.** `evals/` (trigger + negative + seeded-defect), `eval-emit`, README, `claude plugin validate`, footprint measurement, optional `derail-matrix` workflow, AGENTS.md rules (version bump on every shipped change).
**M6 — parity & retire.**

**Safe to delete the three skills when ALL hold:**
1. **Ledger complete (mechanical):** the row-level ledger is generated from the source files; the coverage check confirms **every source heading and table/bullet row** has a destination or a recorded D with reason; zero unmapped.
2. **Behavioral parity on seeded fixtures:** run old skill vs new plugin on the same fixtures (bash CLI with ~10 planted defects, tiny stdlib MCP server with planted defects, a SKILL.md with planted S/M/O/C/T defects + script). Recall(new) ≥ recall(old); zero findings that fail `check findings` (no fabricated evidence).
3. **Derailment parity:** the new loop reproduces a known derailment the old skill would catch, and demonstrably catches a **T1** the old Mode A/C could not.
4. **Three-project walkthrough (§9) passes** in fresh sessions.
5. **Self-audit:** `/agentic-maker:audit` on the plugin is clean; footprint within budget; `claude plugin validate --strict` clean; `claude plugin eval` (if available) trigger/negative cases pass with positive Δ vs baseline.
6. **Cold install** in a fresh config dir works; `doctor` degrades correctly with python3/herdr/rg removed from PATH.
7. Old repo snapshot tagged (git history is the archive). Then delete.

---

## 12. Unknowns to resolve in M0 (flagged, not guessed)

| # | Unknown | Why it matters |
|---|---|---|
| U1 | Clean-room recipe for **subscription** auth for non-plugin targets (CLI/MCP): `--bare` needs an API key *and* drops the skill listing; candidates `--setting-sources`, `--strict-mcp-config`, temp `CLAUDE_CONFIG_DIR` (does it lose login?) | isolation claim, §6.5 |
| U2 | Does `--plugin-dir` + `--add-dir` skill loading behave the same with and without `--bare`; does `--plugin-dir` give the worker the same skill listing a real install does? (see U14) | skill/plugin targets |
| U3 | Does main-thread `stream-json` carry thinking text? (docs show it only with `--forward-subagent-text` for subagents) | "what the agent believed" |
| U4 | Skill-scoped `hooks:` inside **plugin** skills: registered? `${CLAUDE_PLUGIN_ROOT}`/PATH available to their commands? shown in `/hooks`? | H2 placement |
| U5 | `!`cmd`` and `$ARGUMENTS` in user-invoked DMI skills vs swiftui AGENTS.md's "do not run on the Skill-tool path"; `allowed-tools` effect | skill authoring style |
| U6 | herdr: `agent get` → `.agent_session.value` → transcript path for claude/codex; where **agy** stores transcripts (`~/.antigravity`? `~/.config/agy`?) | trace source 1 for live runs |
| U7 | `Ctrl+O` per harness (claude viewer; codex ?; agy unfold) and whether `agent read` sees it; what `HERDR_ENV` is | harness notes |
| U8 | herdr 0.9.5 JSON shapes vs old scripts' (`.result.pane.id`) | stale-reference check |
| U9 | `claude --bg` + `claude agents --json`/attach as a no-herdr live runner; wait without polling? | runner portability |
| U10 | `claude plugin eval` available on the installed build (a `claude update` may be needed) and the best grader mix for our own trigger cases | `eval-emit`, our `evals/` |
| U11 | Agent `skills:` preload of a `user-invocable:false` skill in a plugin agent | trace-reader design |
| U12 | Measured always-on footprint of the 3 descriptions | budget |
| U13 | `claude plugin eval --keep-temp`: does the kept sandbox hold a readable session transcript (path, format, thinking)? Can a generated suite be driven without `--scaffold`? | `eval` runner = clean room with subscription auth |
| U14 | Skill names/listing under `--plugin-dir` vs an installed plugin (`<dir>:<skill>` vs `<plugin>:<skill>`) | validity of T1–T3 results |
| U15 | `Stop` hook inputs: `background_tasks` populated while a headless rerun / herdr `agent wait` runs; `session_id` stable across the orchestrator's turns | H2 false-block avoidance |
| U16 | Whether `claude -p` workers launched from inside an orchestrator session inherit its hooks/pointers (they must not) | H2 isolation, contamination |

---

