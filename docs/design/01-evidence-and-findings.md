> Part of the `agentic-maker` plan · [README](README.md)

# Plan: `agentic-maker` — a native Claude Code plugin for designing agent-facing tools and testing them by derailment

Name: `agentic-maker` (open question Q1, resolved by the repo name). Status: **plan only — nothing is built.** This document is one part of the split plan in this folder; `§` references below point into the other parts (see the section map in the README).

---

## 0. Context

Three skills in `yigitkonur/skills-by-yigitkonur` — `audit-agentic-cli`, `audit-agentic-mcp`, `audit-skill-by-derailment` — are to be deleted and replaced by one plugin. Two jobs: (1) **design/optimize agent-facing tools** (CLIs, scripts, MCP servers/tools, and skills as interfaces); (2) **test them against real agent behavior** with the derailment method (fresh agent → read the whole execution → find drift → fix the *cause* → rerun). It must be native from day one, language-agnostic, and leave room to grow.

**Evidence base (all read, not summarized from the web UI):** every file of the three skills (`SKILL.md`, 7+34+7 references, 8 scripts, `openai.yaml`) via `gh api`; `plugin-swiftui` (manifest, hooks, commands, agent, orchestrator skill, shared refs, lint architecture, eval harness, CI, AGENTS.md; the 1,857-file catalog skipped as data); the installed `herdr-conductor` plugin (skill, 13 references, agent, hooks, evals) and the live `herdr 0.9.5` / `codex` / `agy` `--help`; Claude Code docs fetched as raw markdown 2026-10-20 (plugins/components, skills, hooks, sub-agents, workflows, CLI reference, headless, sessions, plugin-evals, dependencies, mods). Three Haiku inventories of the 66 reference files were used for completeness; the 5 MCP files whose inventories were truncated (security, session-and-state, schema-design tail, caching-economics, client-compatibility) were re-checked by heading.

---

## 1. Findings that change the design (read these first)

1. **`herdr` is already a plugin of yours** (`herdr-conductor`, installed), with a stricter operating model than the old skill: *never poll; one command, one reply; agents interactive only via `agent start`; never prompt/key/close the session's own pane (a guard hook denies it); agent report = claim, machine = witness.* The old derailment skill contradicts it in three places: a **fallback polling loop**, **workers told to `herdr agent prompt $COORDINATOR_PANE_ID`** (the guard denies prompts at the caller's own pane), and **JSON paths** (`.result.pane.id`) that differ from 0.9.5's (`.result.root_pane.pane_id`, per conductor — *verify*). Native design: don't re-document herdr; defer syntax to `herdr … --help` / conductor; the worker reports through **files on disk**, the coordinator uses a background `agent wait`.
2. **`Ctrl+O` is not one thing.** The old skill describes AGY's unfold. In Claude Code docs, `Ctrl+O` toggles the **transcript viewer** (detail + timestamps + model; it is a *toggle* — blind-sending it can collapse a view that was open). Codex's behavior is **unverified**. Better trace sources exist: Claude `stream-json` (headless) or the session JSONL at a **known** path (`--session-id <uuid>` → `~/.claude/projects/<cwd-slug>/<id>.jsonl`; docs warn the JSONL format is internal and changes between versions), Codex `exec --json` / `~/.codex/sessions/…`, agy `-p --output-format stream-json`. `Ctrl+O` + `recent-unwrapped` scrollback stays as the fallback (agy at minimum). So the invariant is reframed from "toggle Ctrl+O" to **"never judge from a view that hides what the agent did"** — trace sources ranked by trust (§6.3).
3. **Old Mode A/C hand the worker the skill's path** ("There's a skill for this at X. Read the SKILL.md…"). That bypasses the layer where most real skill failures start — *whether the skill is chosen at all*. This is the taxonomy's own `O6` (harness-induced drift) committed by the harness. Native scenarios use **everyday prompts that never name the target**, and a new root-cause family **T (trigger)** exists (§6.6).
4. **Mode A asks the worker to self-annotate `[STUCK]/[GUESSED]…`** — self-report, biased, and it changes the agent's behavior. In the native loop the **reader** assigns markers from the trace; self-annotation survives only as an optional cheap mode with its bias documented.
5. **`claude -p --bare` cannot be the clean room.** Bare mode (a) "never reads OAuth credentials or the system keychain" (needs `ANTHROPIC_API_KEY`/`apiKeyHelper`) and (b) **sends no skill listing** (headless docs: it "doesn't get the list of available skills") — so T1–T3 trigger testing is impossible in it even with a key. The better candidate is **`claude plugin eval`'s isolation**: each run gets a temp home/working dir/config, a `claude -p` child with *only the target plugin loaded*, an allowlisted environment, OS sandboxing, the user's normal auth, and `--keep-temp` retains the sandbox (does it contain a readable session transcript? U13). So skill/plugin targets get a new runner `eval` (§6.2). Where no clean room is proven, runs record a **contamination report** instead of claiming isolation.
6. **Claude Code now has `claude plugin eval`** (trial runs with a no-plugin baseline, `tool_used: Skill` graders, regex/file/llm graders). It overlaps the *trigger* half of derailment and is the right **regression** tool; derailment is the **forensic** tool. They compose (§6.9). Its "early access" message means an older build (`claude update`), not a gate → optional, availability checked by `doctor` (U10).
7. **Real defects in the sources** (found while reading; fixed at migration, never carried): 25 listed in Appendix B — e.g. exit-code taxonomy 0–7 vs 0–8 and a batch response using `exit_code: 3` for "partial"; error JSON on stdout in one file, stderr in another; the MCP SKILL.md's script path is nested wrong (`skills/audit-agentic-mcp/skills/audit-agentic-mcp/scripts/…`); two client matrices that disagree (Cursor roots ignored vs native); `audit-worker-pane.sh` hard-codes `mp4/mp3/png` and `__TAKE_RESULT_JSON` (domain leakage from the video-flow skill); the "20–30 friction points" heuristic reads as a quota, which invites fabricated findings.

8. **An adversarial review of the first draft (Appendix C) corrected the draft against the docs**, all verified: plugin agents cannot path-restrict `Write` (so a "read-only" reader with `Bash`+`Write` is not read-only); `bin/` is on PATH for the Bash tool, **not** for hook processes (hooks must call `${CLAUDE_PLUGIN_ROOT}/bin/agentic-maker`); a failing `!`cmd`` aborts the **whole** skill invocation (append `|| true`); `context: fork` has no `AskUserQuestion`, no history, and runs in the background unless `background: false`; an `allowed-tools` grant clears at the user's next message; subagents *can* nest (3 layers) — my draft said they can't; "plugin eval is currently in early access" means *your build predates GA* (`claude update`), not that it is gated; and handing the worker's task to `herdr-conductor:herdr-worker` would append done-checks/marker/"you are a worker" text to the brief — the very O6 contamination the plan bans.

---

## 2. What each source skill is really about

| Skill | Core mental model | Heuristics that carry the value | What it quietly assumes |
|---|---|---|---|
| **audit-agentic-cli** | A CLI is an agent's API. *stdout = data, stderr = operator, exit code = semantic class, and all three agree.* | 5 core checks; severity in **agent** terms (can the agent parse/continue/avoid side effects?); one envelope `{ok,result,error{class,code,message,retryable,suggestion},schema_version}`; repair **build order** (pure JSON → errors+exit codes → non-interactive/dry-run → repair loops → discovery → async); iterative repair loop with `next_action.command`; "fix the CLI before blaming the architecture" | POSIX shell; CLI safe to probe with `--help`; its scripts only text-scan help (explicitly "not an agent-readiness proof"); sibling skills `linear-cli`, `run-railway`, `build-mcp-*`, `test-by-mcpc-cli` exist; `jq`, GNU `timeout`; Go/Cobra-centric examples |
| **audit-agentic-mcp** | A tool description/schema/response is **prompt engineering**; the unit of design is user intent, not endpoints; first decide whether MCP should exist. | 15 hard rules (intent tools, flat 3–6-param schemas, curated responses, `isError` vs protocol errors, server-side validation, Streamable HTTP, progressive discovery past ~20 tools, descriptions as prompts, capability-gate sampling/elicitation/roots, OBO not passthrough, verify after every edit); 2 modes (audit existing / architect new via 12-question interview); thresholds as **diagnostic cues, not verdicts**; freshness checks | TS/Python SDKs and FastMCP; regex finds `server.tool(`; `rg`/`tree`; spec 2025-11-25; model/client/vendor facts dated 2025-12…2026-04 (stale-prone); the author's companion skills |
| **audit-skill-by-derailment** | A skill is a **program executed by an LLM**; every drift is a *text* defect (S/M/O/C taxonomy, 21 codes); test it by running it for real and reading the run. | **Fix the reason the agent drifted, not the agent** (rewrite the controlling text; no appended do/don't); anti-self-report (bits on disk > prose); `[NICE]` lines are load-bearing; compound-P0 (3+ P1 in one phase); two-tier run → forensic reader; no errata files; fix-pattern per root cause | herdr + AGY as the worker; macOS (`stat -f`); `invoke_subagent` (AGY-specific); worker→coordinator callback via `herdr agent prompt`; media-file receipts from a video skill |

The unifying idea (and the reason one plugin is right): **all three are about the same object — an *agent-facing surface* (CLI, script, MCP server/tool, skill) whose text/affordances shape agent behavior.** Design knowledge says what good looks like; derailment shows what agents actually do; each corrects the other.

---

## 3. What `plugin-swiftui` teaches (patterns kept, mistakes not copied)

**Deliberate, reusable:**
- **Engine ≠ steering.** A real CLI (`swiftui-ctx`) holds the knowledge; skills are thin drivers. The CLI follows the contract it preaches (envelope with `next_actions` = literal follow-up commands; semantic exit codes; `doctor`; exit 5 "STOP, don't fabricate"). → `bin/agentic-maker`, dogfooding the audit rules.
- **`bin/` shim on PATH + self-bootstrapping wrapper** (cache, lock, degrade with a doctor hint). Avoids `${CLAUDE_PLUGIN_ROOT}` fragility (their AGENTS.md: substitution and `!`/`$ARGUMENTS` were unreliable on the model-invoked path).
- **Locate vs judge.** The lint engine only *locates*; the agent *reads and judges*; two tiers (grep always, ast-grep optional) with a **parse probe** so a silent parse failure can't pose as a clean file. → our `scan` and trace normalizer never silently drop (`unparsed: n`).
- **Steering scan** (`audit-scan.py` + `audit-signals.tsv`): cheap relevance routing so only applicable audits run; adding a domain = one TSV row. → `surfaces.tsv`.
- **Orchestrator skill = ordering + parallelism + aggregation only; rules live in owners; shared references "point in, never restate"**; filesystem is the only inter-subagent channel; fixes serial, detection parallel; byte-identical finding schema; `_SUMMARY.md`.
- **Fix-safety protocol** (clean tree, findings-first, one commit per finding, never weaken the check, **verify after fix with fresh evidence**) → adopted for the derail fix step.
- **One non-blocking hook**, static grep, kill switches, data file kept in sync by CI. → our hook bar (§5).
- **Eval harness** (grounded vs baseline, deterministic oracles) and CI that guards *rule rot* (self-test of lint rules) and manifest strictness.
- **AGENTS.md maintenance rules** (bump `version` on any shipped change; no manual path fields in `plugin.json`).

**Not copied:** 33 skills with ~500-char descriptions each (every model-invocable description is in context every turn); the same four workflows duplicated across `commands/`, `skills/`, and a Codex package; committed build output (2,214 files under `plugins/`); a 100 MB catalog in the repo. Our always-on footprint target is **2 skill descriptions + 1 agent description** (§5).

---


## Appendix A — plugin-swiftui choices, one line each (reuse / skip)
Reuse: CLI-as-engine with `next_actions`; `bin/` shim; locate-vs-judge; parse probe; relevance TSV; orchestrator = order+parallelism+aggregate only; shared refs point-in-never-restate; fix-safety 8 points; one non-blocking hook with kill switches; eval harness + rule-rot CI; AGENTS.md rules (version bump, no manual path fields). Skip: skill sprawl, duplicated command/skill/Codex copies, committed build output, giant data in repo.


---
### Claims to verify (M0)
- Finding 1 / U8: herdr 0.9.5 JSON shapes (`root_pane.pane_id` etc.) vs the old scripts' `.result.pane.id`.
- Finding 2 / U6, U7: where each harness stores its session record; what `Ctrl+O` does in Codex and agy; whether `herdr agent read` sees a toggled view.
- Finding 5 / U1, U13: subscription-compatible clean room; whether `claude plugin eval --keep-temp` leaves a readable transcript.
