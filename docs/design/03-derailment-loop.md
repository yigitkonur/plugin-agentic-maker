> Part of the `agentic-maker` plan · [README](README.md)

## 6. The derailment loop as a native feature

### 6.1 Shape

`/agentic-maker:derail <target> [--scenario NAME] [--runner headless|eval|herdr|existing] [--harness claude|codex|agy] [--isolation clean|in-situ] [--rounds N]`

Front half varies by **source of the execution**; back half is identical.

```
 FRAME ─► LAUNCH/ATTACH ─► WAIT ─► COLLECT ─► NORMALIZE ─► RECEIPTS ─► READ ─► CHECK ─► SYNTHESIZE ─► FIX ─► RERUN ─┐
 target,   headless|eval|   bg wait  trace +   trace.norm   disk        trace-   verbatim  dedupe,       source   fresh   │
 scenarios, herdr|existing  no poll  env.json  + trace.md   evidence    reader   quotes,   matrix,       rewrite  session ◄┘
 COST PREVIEW                                               (receipts)  (JSON,   fields    compound-P0   (single  (H2 guards
 + confirm                                                              Read/    valid     NICE-guard    writer)  this edge)
                                                                        Grep/Glob)
```
Old modes map: **A** (synthetic) → `headless` (a real fresh process, not a same-session subagent that inherits the parent's skills/CLAUDE.md; the old "cheapest possible smoke check" survives as `--runner headless --max-turns 8`); **B** (existing panes) → `--runner existing --from <session-id|pane|file>` (no launch; reader + synthesis only; fleet matrix = repeat back half); **C** (herdr worker → forensic subagent) → `--runner herdr`. **FRAME ends with a cost preview** (rounds × scenarios × runs, runner, estimated spend, readers) and asks before spending — money is a confirm-first action.

### 6.2 Runners

| Runner | Spawn | Wait | Best for | Notes |
|---|---|---|---|---|
| **headless** (default for inner rounds) | `claude -p "<prompt>" --output-format stream-json --verbose --include-hook-events --session-id <uuid> --max-turns N --max-budget-usd B --plugin-dir <target>` / `--mcp-config F --strict-mcp-config`; cwd = fresh **temp** workspace from scenario fixtures (never the target project, so project-keyed hooks/pointers can't see it). Codex: `codex exec --json -C <dir> -s <sandbox>`; agy: `agy -p --output-format stream-json` | process exit | cheap, parallel, structured, CI-able | `--bare` is **not** the isolation (no skill listing, API-key only). Permission mode, `--allowedTools`, turn and budget caps explicit and recorded; destructive-capable targets only under a sandbox (`--settings` sandbox) or on throwaway fixtures — never bypass permissions on real data |
| **eval** (skill/plugin targets; clean room) | Generate a throwaway eval suite from the scenario (`prompt.md` + graders compiled from receipts) and run `claude plugin eval <plugin> --runs 1 --ablation none --keep-temp --json --max-cost-usd C` | process exit | The one clean room that works with subscription auth and keeps the **skill listing**, so T1–T3 are testable; OS sandbox; optional with/without Δ | Graded, not forensic: we still need the kept sandbox's session transcript for the reader (**U13**). If unreadable, `eval` is used for trigger statistics only and `headless` for forensics |
| **herdr** (live; final confirming round; interactive/dialog scenarios; agy) | Follow `herdr-conductor`'s **rules directly**: `tab create --no-focus`, `agent start <name> --kind <k>`, read the screen after start (trust dialogs), `agent prompt … --wait --timeout`, background `agent wait`, never poll, never touch own pane. Do **not** hand the task to `herdr-worker` (it appends done-checks/marker/"you are a worker" to the brief = contamination) | `agent wait` (state), then screen read; `completion_seq` | Fidelity to what a user sees: trust dialogs, approvals, TUI quirks, multi-turn, harnesses without a good headless mode | The worker's brief is the scenario prompt **verbatim** — no coordinator callback; deliverables go to files; the orchestrator verifies on the machine. The conductor's guard denies bypass flags, so workers *will* hit approval dialogs: scenarios declare `approvals:` (dialogs the run may answer, with keys); any other dialog is recorded as a **finding** (real user friction) and the run ends `needs_decision`. The mechanics are agent-driven, never a script (conductor rule: a chain that runs unattended also fails unattended) |
| **existing** | none | none | Post-hoc audit of sessions you already ran (old Mode B), fleet comparison | Never prompt the live agent during capture (contaminates evidence); a corrective nudge to finish deliverables is allowed only *after* capture and only if the user wants the work done |

*Recommended default (Q2):* **headless for rounds 1…n (or `eval` for skill/plugin targets if U13 passes), one herdr live round to confirm** (matches "done = watched in its real form").

### 6.3 How the execution is read (trace sources ranked by trust)

1. **Harness-written structured record**: Claude `stream-json` events (documented), or session JSONL at the pre-assigned path; Codex `exec --json` / rollout files; agy `stream-json`. Complete tool args, results, exit codes, hook events.
2. **Terminal scrollback with verbose view**: `herdr agent read <t> --source recent-unwrapped --lines N` (`recent-unwrapped` mandatory — soft wraps break regexes). Make the view verbose **conditionally**: probe the scrollback for markers of expanded output first, toggle (`ctrl+o`) only if collapsed, re-probe. Per-harness behavior (Claude = transcript *viewer*, AGY = unfold, Codex = unverified) is recorded in `harnesses/<name>.md` **from observation, dated** (M0, U7).
3. **The agent's own report** — a claim; never evidence.

`agentic-maker normalize` turns any source into one format: `trace.norm.jsonl` (`n, t, role, name, args, text, exit, truncated, src{file,line}`) and `trace.md` (compact, line-numbered `[n]` — the evidence references). It reports `unparsed: n` and unknown event types instead of dropping them (swiftui's parse-probe rail). Adding a harness = one adapter. Claude's JSONL format is internal → adapter is tolerant + self-checking; prefer `stream-json`.

### 6.4 Scenarios (the part that grows without restructuring)

Files in the target project: `.agentic-maker/scenarios/<name>.md` (committed; they are the regression suite in prose).

```
---
name: add-json-output          kind: skill|plugin|cli|mcp
target: ./skills/x | cli:mycli | mcp:./.mcp.json
build: cargo build             # optional: how to produce the artifact (Rust/Go/TS need one)
bin: target/debug/mycli        # optional: resolved binary path (not the crate name)
env: [FOO_API_BASE]            # allowlist of env vars passed to the worker (no secrets by default)
harness: claude   runner: headless   isolation: clean|in-situ
max_turns: 40     timeout_s: 600     budget_usd: 2
interactive: false
approvals: []                  # dialogs a live run may answer: [{match: "Do you trust", keys: "enter"}]
---
## Prompt            (verbatim what a user would type; never names the target unless a user would)
## Implicit constraints   (hidden from the worker; the reader checks them: output dir, no destructive ops…)
## Fixtures          (script or files that seed a fresh workspace)
## Receipts          (what must be true afterwards + how to check; the anti-self-report ledger)
```
Receipt kinds (generalizing the old media-specific checks): `exists`, `nonempty`, `type` (magic/`file`/parse), `jq`/schema, `cmd` (command + expected exit), `mtime-in-window`, `unchanged`, `no-extra-files` (path drift). *No media types or delimiter strings are built in* (that was the video skill's leak).

Authoring guide (kept from Mode A): "everyday user energy + 2–3 implicit constraints"; add one **ambiguity** scenario, one **failure-injection** scenario (missing prerequisite, stale flag), one **scale** scenario (O4). `derail` proposes three if none exist.

### 6.5 Clean room vs in-situ

`clean`: only the target is visible (for skills/plugins via the `eval` runner's isolation if U13 passes; for MCP `--strict-mcp-config`; no user CLAUDE.md, no other plugins). `in-situ`: the user's real setup — tests **collisions** (a new skill's description competing with 30 others), which is itself a real failure class (T2). Every run writes `env.json` (versions, flags, permission mode, visible skills/plugins/MCP/CLAUDE.md = **contamination report**), so we never claim isolation we didn't get. Rounds 1…n clean when achievable; the confirming round in-situ. Note for T-tests: `--plugin-dir` may name skills `<dir>:<skill>` rather than the installed `<plugin>:<skill>`; the listing the worker saw is recorded and compared with what a real install produces (**U14**).

### 6.6 Finding the drift — the reader and the taxonomy

`trace-reader` (**tools `Read, Grep, Glob` only** — genuinely read-only, because plugin-agent `tools` can't path-restrict `Write`; disk checks are computed *before* it runs by `agentic-maker check receipts`, so it never needs `Bash`; `skills: [derailment-method]`; `effort: high`; **returns the findings as JSON in its final message**, which the orchestrator saves per run as `findings/<scenario>-<run>.json` — one file per reader, so attribution is never ambiguous) reads `trace.md` in chunks and `receipts.json`, then searches **dimensions** (breadth prompt kept from the "20–30 friction points" idea, **without a quota**; "none found in dimension X" is a valid answer): trigger, discovery (did it read referenced files? orphan refs), syntax/flags, thresholds, selectors/resilience, mental-model drift (C1–C4), gating slack, output paths, stale docs, recovery, budget.

Signals it looks for (from `herdr-pane-audit` heuristics, generalized): re-reads of the same section; `--help` instead of running the thing (C3); long deliberation before an ambiguous step (M1/M5); error → workaround invention (O1/O5); steps in the text that never appear in the trace (C4); "done" while receipts fail (C1); files created in unexpected places (M2/S3); questions to the user the text should answer (S1/M5); two instructions in conflict—which one won (S2); retry with unchanged hypothesis (C5).

**Finding record** (one schema for all targets): `id, marker, severity, root_code, layer(trigger|discovery|execution|recovery|completion), trace_refs[], quote, belief (what the agent believed at that moment) + belief_source (`observed` = from a thinking block in the trace; `inferred` = from preceding observations — U3 decides how often we get `observed`), controlling_text{file,lines,quote|ABSENT}, fix{kind: rewrite|delete|inline-at-point-of-use|restructure|add-probe, patch}, rerun_predicate{type: tool_used|regex|not_regex|order|reads_file|exit_code|judged, …}, confidence`. Predicates are **machine-checkable over `trace.norm.jsonl`** (mirroring eval grader types) wherever possible; `judged` is allowed but labelled and never counts as a clean rerun on its own.

**Taxonomy:** keep the 4 markers `[STUCK][BROKE][GUESSED][NICE]`, P0/P1/P2, compound-P0 (≥3 P1 in one phase), and all **21 codes with stable IDs** (S1–S5, M1–M6, O1–O6, C1–C4). Add (marked *new*): **T1** not triggered, **T2** mis-triggered/collision, **T3** over-triggered; **M7** ambiguous tool boundary; **O7** response misread; **O8** budget blowup (definitions/responses); **C5** retry blindness/loop. (Q5.) Without T, the loop can't see the most common skill failure; M7/O7/O8/C5 are what CLI/MCP derailments produce.

### 6.7 Fixing the cause (the central principle, operationalized)

- Every finding must name the **controlling text** (the sentence/example/routing row/`--help` line/tool description/error message — or its *absence*) and say what the agent believed because of it.
- **Source Rewrite First:** rewrite or delete the controlling text so the right path becomes natural; add a rule beside bad text only if both are needed (old fix-patterns §11). Fix-pattern catalog kept (prerequisite surfacing, threshold concretization, path reconciliation, output location, execution method, format alignment, scaling guidance, conditional gating, schema at point of use, harness alignment, two-tier verification, staged deprecation, pre-flight probe, rigid phase gating) — **extended** for CLI/MCP: rewrite the error message, add a `--probe`/`--dry-run`, put the example in the description.
- **`agentic-maker check findings`** (before any edit): every `trace_refs` event exists; every `quote` appears **verbatim** in the cited events; fields and codes valid; `ledger fix <id>` accepts only verified ids. *The reader's claims are leads until the bits check out* — the anti-sycophancy law one level up.
- **`agentic-maker check diff`** (after each edit, on the **applied** diff, not the proposal): flags `patch-by-rule` — hunks that only add imperative text ("always/never/don't/make sure/important:/must") next to unchanged controlling text. It does **not** fire when `controlling_text` is `ABSENT` (the right fix is then an addition) or when the hunk rewrites/deletes the quoted text. A flag requires a recorded justification, not silence.
- **`[NICE]` guard:** the reader emits `nice` quotes; `agentic-maker check nice` fails the round if an applied diff removed one without a superseding finding.
- **Single writer:** readers are read-only and propose; the orchestrator applies (serial, one commit per finding if git, clean-tree gate, never weaken a check — swiftui fix-safety, adapted). *No errata files:* runs/ artifacts are disposable working evidence (gitignored); the deliverable is the corrected source (+ the committed scenarios).
- **Rerun in a fresh session**; attribute with the machine-checkable `rerun_predicate`; one root cause per rerun when feasible.

### 6.8 Stop criteria and budgets

Stop when: no P0/P1, receipts pass, **2 consecutive clean runs** (non-determinism), or `--rounds` (default 5) / the **run-level `budget_usd_total`** is reached → report OPEN/UNVERIFIED honestly. The ledger tracks one total budget across *everything* — workers (`--max-budget-usd` / `--max-cost-usd`, both client-side estimates that can overshoot), readers (count × chunks, capped by `readers_max`), and live herdr runs (no native cap → the time limit plus a per-run estimate) — and shows it at the cost preview. Every run has a time limit; a crash/timeout/2 min silence = failed run, not a pass. Report: ledger of rounds, what text changed (diffs), evidence refs, residual.

### 6.9 What it can test, and how it composes with `claude plugin eval`

| Target `kind` | Exposure to the fresh agent | Primary lens |
|---|---|---|
| `skill` | skill dir loaded (`--plugin-dir`/add-dir), prompt never names it | T1–T3, reading of references, step skipping, guessing, path drift |
| `plugin` | the plugin dir (multiple skills/agents/hooks); `--include-hook-events` | cross-skill routing, hook firing/noise, subagent use, **footprint** — also how **agentic-maker tests itself** (M1 dogfood) |
| `cli` / script | binary on PATH, only `--help` (cold) or `--help`+skill (assisted) | discovery from help, stdout/stderr misparses, exit-code misreads, hangs/prompts, retry loops (M7/O7/C5) |
| `mcp` | `--mcp-config` + `--strict-mcp-config` | tool selection (M7), argument errors, response misreads, error recovery, **token cost** (O8) |

After convergence on a `skill`/`plugin` target, `agentic-maker eval-emit` can write the scenario as a `claude plugin eval` case (`tool_used: Skill` + receipt graders + no-plugin baseline) into the target's `evals/` — derailment *finds*, eval *guards* in CI. Optional; needs a current Claude Code build (`claude update`) — U10.

---


---
### Claims to verify (M0)
- U1/U13 clean-room recipes; U3 whether main-thread `stream-json` carries thinking (decides `belief_source`); U9 `claude --bg` as a no-herdr live runner; U14 skill naming under `--plugin-dir`; U16 workers must not inherit the orchestrator's hooks/pointers.
