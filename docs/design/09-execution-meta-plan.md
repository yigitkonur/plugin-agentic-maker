# 09 — Execution meta plan: from this plan to a public plugin

> Nav: [README](README.md) · prev: [08 open questions](08-open-questions-and-readback.md)

**Status:** written 2026-10-20, immediately before execution starts. This file says *how we build*; files 01–08 say *what we build and why*. Where this file and 01–08 disagree, this file wins (see §1, amendments A1–A10) and the build edits 01–08 in the repo copy.

**End state:** `github.com/yigitkonur/plugin-agentic-maker` is public, and a fresh clone of it validates, installs from its own marketplace into an empty config dir, and runs a skill. Every capability the README advertises was watched working; anything that was not is labelled UNVERIFIED or left out.

---

## 0. Rules of engagement

1. **One ledger, ten rows, owned by the main thread.** Row 0 is the goal; rows 1–9 are in §8. A row is `PASS` only with pasted evidence (command, exit code, first lines of output, file path). A row that cannot be run is `UNVERIFIED` with the reason, never filled from memory.
2. **Failure protocol:** one plain rerun (passes → note flaky); then up to three fixes, each with a new hypothesis, rerunning that row only; still failing → read the stuck-row guide. Every run has a time limit; a crash, a timeout or two minutes of silence is a failed run.
3. **Build the smallest thing that runs, then watch it run.** No test suite before the thing works live; fixtures and expected outputs are *recorded from what the tool really did*, after reading the diff and judging it right.
4. **Boundaries.** Writes go to exactly three places: `plugin-agentic-maker/` (the repo), `docs/design/` (this plan, append-only after today), and `/tmp/am-*` scratch. Never touch sibling `plugin-*` or `*-plan` folders, `~/.claude` settings, or the three source skills (the user deletes those, not us). herdr: only tabs this run created, closed by this run; never the session's own pane.
5. **Spend cap.** Auth is the claude.ai subscription (no API key), so there is no per-token bill, but there are usage limits. Every headless run passes `--max-turns` and `--max-budget-usd`; estimates are appended to `<scratch>/scratch/budget.tsv`. **Soft stop at an estimated USD 25 total** across all headless/eval/herdr runs: stop, report, continue only if the user says so. Workers default to `--model sonnet` (Haiku for smoke checks); readers use the plugin's own agent setting.
6. **Delegation.** The main thread keeps the ledger and writes the novel, central parts itself (CLI, derailment method, derail skill, reader). Content migration (the ~66 reference files) goes to at most five `sonnet-high` subagents in parallel, each with a self-contained brief (§5); their output is checked by scripts, not trusted.
7. **No claim without a witness.** An agent's report is a claim; the machine is the witness (`ls`, `jq`, exit codes, a rerun).
8. **Commits** per step, in the repo, under the GitHub noreply identity (`<the GitHub noreply address>`), conventional messages, with the required `Co-Authored-By` trailer. No tokens, personal paths or emails ever land in a commit (`scripts/check.sh` greps for them from S3 on).

---

## 1. Decisions fixed before any work (amendments to 01–08)

| # | Decision | Why |
|---|---|---|
| **A1** | **Plugin name `agentic-maker`** (repo `plugin-agentic-maker`). Commands `/agentic-maker:audit`, `:design`, `:derail`; CLI `bin/agentic-maker`; per-project dir `.agentic-maker/`. The working name `toolsmith` used in the original plan was renamed to `agentic-maker` mechanically in this copy of the design docs. Resolves **Q1**. | The user named the repo; the user's other repos follow `plugin-<name>` → plugin `<name>` (`plugin-sentry` → `sentry`). |
| **A2** | **The repo root is the plugin** (like `plugin-sentry`): `.claude-plugin/plugin.json` + `marketplace.json` (`source: "."`), MIT license, `AGENTS.md` maintainer rules, `scripts/check.sh` gate, `.github/workflows/ci.yml`. The plan docs are copied to `docs/design/` (renamed per A1) at S0 and **edited only there from then on**; this folder gets a pointer line at the end. | One source of truth; matches the user's existing repos so they can maintain it the same way. |
| **A3** | **Python 3.9 floor, stdlib only** for `bin/` and `lib/` (the user's convention; `/usr/bin/python3` is 3.9.6 here, so the floor is testable). | Zero install friction; same bar as `plugin-sentry`. |
| **A4** | **Row-level parity = three mechanical checks, not "every bullet".** (i) heading coverage — *hard gate*: every H1–H3 in every source file maps to a destination (provenance marker) or a recorded D with a reason; (ii) every table first-column key maps; (iii) *token survival* — backticked identifiers, numbers/thresholds and rule numbers found in the sources must appear in the new corpus or in the D list; each miss is restored or explained. Bullets have no stable identity, so they are covered by (iii), not by a per-bullet table. | Amends §10/§11 gate item 1, which over-promised. |
| **A5** | **Scenario front matter is flat `key: value`; a value starting with `[`, `{`, `"` or a digit/`true`/`false`/`null` is parsed as JSON, anything else is a string.** No YAML dependency. | Stdlib only; deterministic parse; the §6.4 example keys stay. |
| **A6** | **Old-vs-new recall (gate item 2):** the old scripts are deterministic, so they run on the fixtures directly; agent-level comparison is done once per surface on one fixture each, and the limitation (n=1) is stated in the parity report. | Full agent runs of 3 old skills × 3 fixtures × repeats costs more than it proves. |
| **A7** | **README has a status table:** each feature → `watched working` / `fixture-tested` / `documented only`. Nothing is advertised beyond its row. | Honesty is cheaper than a retraction. |
| **A8** | **H2 lives in `skills/derail/SKILL.md` frontmatter (U4 passed in M0)**, with an early-exit script; kill switch `AGENTIC_MAKER_HOOKS=off`. Keep H2 only if M1 dogfooding shows it blocks a real premature "fixed" **or** a seeded one (Q15 default). | §5. |
| **A9** | **Q-defaults adopted as written:** Q2 headless inner rounds + one herdr live round; Q3 soft herdr dependency; Q4 per U1/U13 result; Q5 yes (T1–T3, M7, O7, O8, C5); Q6 `fresh/` with `as_of`; Q7 companions routed only if installed; Q8 exit codes 0–8 (8 = partial); Q9 macOS/Linux/WSL; Q10 no Codex/agy hosting; Q11 optional `eval-emit`; Q12 audit = report only; Q13 workflow deferred; Q14 ship order skill → CLI → live → MCP; Q15 one hook; Q16 reader `Read, Grep, Glob`. The user can still overrule any of these at the end; the final report lists them. | The brief asked for recommended defaults, and "move to action" means take them. |
| **A10** | **MIT license, `Copyright (c) 2026 yigitkonur`**, and CI shaped like `plugin-sentry`'s (Python 3.9 + 3.14 matrix, `claude plugin validate`, offline checks). | Matches the user's other public plugins; flagged in the final report as a default. |

---

## 2. Environment facts (checked 2026-10-20, not assumed)

`gh` is logged in as `yigitkonur` (scopes include `repo`, `workflow`); `yigitkonur/plugin-agentic-maker` does **not** exist yet. `claude 2.1.302`, auth = claude.ai subscription. `herdr 0.9.5`, `codex`, `agy`, `rg`, `jq`, `git`, `node` present; `shellcheck` absent. `python3` = 3.14.7 on PATH and `/usr/bin/python3` = 3.9.6. `claude plugin` has `eval`, `details` (component inventory and **projected token cost** — a native footprint meter for U12), `validate`, `configure`. Docs scratch copies exist in `/tmp/cc-docs-scratch/`.

---

## 3. The steps (S0–S10)

Each step: **Do** → **Proof** (what gets pasted into the ledger) → **If it fails** → **Commit**. Steps are strictly ordered unless marked parallel.

### S0 — Repo, scratch, sources (no behavior yet)
**Do**
1. `mkdir <workspace>/plugin-agentic-maker && git init -b main`; repo-local `user.name=yigitkonur`, `user.email=<the GitHub noreply address>`.
2. Scratch: `<scratch>/src/` ← shallow clones of `yigitkonur/skills-by-yigitkonur` (the 3 skills) and `yigitkonur/plugin-swiftui`; `<scratch>/spike/`, `<scratch>/scratch/` created. Clones are data: no scripts are run from inside them.
3. Write `LICENSE`, `.gitignore` (`.DS_Store`, `__pycache__/`, `.agentic-maker/runs/`, `.env*`), minimal `plugin.json` and `marketplace.json` (name `agentic-maker`, version `0.0.1`), copy `01–09` + appendices into `docs/design/` and apply A1 rename.
**Proof:** `git log --oneline` shows the first commit; `jq . .claude-plugin/*.json` parses; `diff` shows the rename is the only change in `docs/design/`.
**If it fails:** none expected. **Commit:** `chore: repo skeleton and design docs`.

### S1 — M0 spike: resolve U1–U16 (no plugin code kept)
**Do:** run the experiments in §4 in `<scratch>/spike/`. Each gets: command, trimmed real output, verdict (`TRUE` / `FALSE` / `UNVERIFIED`+reason), and the plan consequence. Write `docs/what-is-true.md`, then **edit `docs/design/*.md`** where a claim turned out false or a branch was chosen (§6 table).
**Proof:** `docs/what-is-true.md` has sixteen rows, none blank; a `grep -c` of `UNVERIFIED` is listed with reasons; the design docs' "claims to verify" footers are updated.
**If it fails:** a spike that cannot run is `UNVERIFIED` and takes the degrade branch in §6; it does not block S2. **Commit:** `docs: M0 spike results (what is true)`.

### S2 — Content contract and migration briefs (before any subagent starts)
**Do**
1. Write `docs/migration-brief.md`: the one canonical exit-code table (0–8, Q8), the error envelope (in `--json` mode success **and** failure go to stdout, stderr is human diagnostics only — resolves defect 4), class enum (adds `usage`, `transient`), pagination field names, the resolutions for each Appendix-B defect 1–22, the file rules (≤ ~8 KB, one decision, stable headings, no model/vendor/price facts outside `fresh/`, no media-type or marker-string leakage, language code only in `frameworks/`), and the **provenance marker** `<!-- src: <skill>/<path>#<Heading> -->` placed above every migrated section.
2. Write `scripts/parity.py` (heading extractor + provenance checker + token-survival report) and run it on the **empty** corpus: it must list every source heading as unmapped (proves the checker can fail).
**Proof:** the unmapped count printed by `parity.py` equals the independently counted number of source headings (`rg -c '^#{1,3} ' …`).
**If it fails:** fix the extractor before delegating anything. **Commit:** `feat(parity): heading/token coverage checker; migration brief`.

### S3 — Skeleton and CLI v1 (row 3)
**Do:** `bin/agentic-maker` (POSIX shim → `lib/agentic_maker/`), five commands, envelope + `next_actions`, one exit-code table:
- `doctor` — tools present/absent, `claude` version, `claude plugin eval` availability, what degrades.
- `run` — parse scenario (A5), render prompt (no marker instructions), cost preview and `--dry-run`, spawn `claude -p … --restricted --strict-mcp-config --plugin-dir <target> --tools … --allowedTools … --permission-mode … --output-format stream-json --verbose --include-hook-events --session-id <uuid> --max-turns --max-budget-usd` (the M0 U1 clean room) with `HERDR_*` scrubbed, in a fresh temp cwd seeded from fixtures; write `env.json` (contamination report from the `system/init` event), raw stream, exit status; `--runner existing --from <file>` ingests without launching.
- `normalize` — stream-json → `trace.norm.jsonl` + `trace.md` (`[n]` refs, `unparsed: n`, unknown event types counted, never dropped).
- `check receipts|findings|diff|nice` — as §6.7.
- `ledger init|status|fix|gate|abandon|close` — session-keyed, H2's brain.
Also: `scripts/check.sh` (compile on 3.9 and 3.14, `claude plugin validate .`, secrets/personal-path grep, link check), five `SKILL.md` stubs and `agents/trace-reader.md` so the plugin loads.
**Proof:** `claude plugin validate .` output; `bin/agentic-maker doctor --json | jq .ok`; a real `run` of a trivial scenario then `normalize` on its stream with the counts pasted; `--json` stdout parsed by `jq` with stderr empty; exit codes for a forced usage error (2) and a missing file (3); both interpreters pass `check.sh`.
**If it fails:** stdlib-only is non-negotiable; fix the code, not the rule. **Commit:** `feat(cli): doctor, run, normalize, check, ledger (v1)`.

### S4 — Derailment core: method, reader, `derail` skill, H2 (row 4)
**Do**
1. `skills/derailment-method/` (SKILL.md + `taxonomy`, `fix-patterns`, `reading-traces`, `evidence-and-anti-sycophancy`, `finding-schema` references; 21 original codes frozen + T1–T3, M7, O7, O8, C5), written by the main thread from the source references; provenance markers on every migrated section.
2. `agents/trace-reader.md` (`Read, Grep, Glob`, `skills: [derailment-method]` if U11 passes, `effort: high`; returns JSON).
3. `skills/derail/` (DMI, hooks per A8) with `references/{loop,scenarios,clean-room,synthesis-matrix}.md` and `runners/{headless,existing}.md`, `targets/{skill,plugin}.md`.
4. Fixture `fixtures/skills/seeded-skill/`: a small skill with planted defects (a description that never matches an everyday prompt → T1; a reference never linked → S4; a step with an ambiguous threshold → M-class; a path that does not exist → S3) and `.agentic-maker/scenarios/*.md` that never name it.
5. Run the loop for real: `/agentic-maker:derail fixtures/skills/seeded-skill` headless, 2–3 scenarios; read with the real `trace-reader`; `check findings`; fix the *controlling text*; `check diff`; rerun fresh; `rerun_predicate` machine-checked.
6. Provoke H2: edit the target, try to close without a fresh trace, show the block, then take an allowed exit.
**Proof:** the run directory listing; `findings/*.json` with `check findings` exit 0; the `git diff` of the fix; the rerun's predicate result (`tool_used: Skill` flipped false→true, or equivalent); the H2 block message copied verbatim; a negative control (a fabricated quote is rejected by `check findings`).
**If it fails:** if the reader cannot reach the seeded defect, the defect is too subtle or the text is wrong — fix `derailment-method`, not the fixture; if T1 is not observable (U14), record it and test T2/T3 only. **Commit:** `feat(derail): method, reader, loop, H2; seeded skill fixture`.

### S5 — Design contract and the CLI side (row 5) — *content batches A run in parallel with S5 code*
**Do**
1. Subagent **batch A** (§5) migrates the CLI references into `skills/agent-interface-design/references/cli/…` and `frameworks/…`.
2. Main thread: `probe cli`, `probe cli-diff`, `scan`/`detect` + `data/surfaces.tsv` (cli rows first), `skills/agent-interface-design/SKILL.md` (contract + routing), `skills/audit/` (CLI path), `references/contract.md` (8 questions).
3. Fixture `fixtures/cli/seeded-cli` (bash, ~10 planted defects: exit 1 for every error, error text on stdout, no `--json`, interactive prompt, hang without TTY, colors with `NO_COLOR`, a destructive subcommand *not* declared safe, and so on) plus a clean twin for false-positive control.
4. Run `/agentic-maker:audit fixtures/cli/seeded-cli` for real; run the **old** `audit-cli-help.sh` on the same fixture for the comparison.
**Proof:** `probe cli --json` output with each planted defect found; the sentinel that proves the destructive subcommand was never executed (its marker file is absent); zero findings on the clean twin; the old script's findings side by side.
**If it fails:** a probe that executes something undeclared is a safety bug: stop and fix before anything else. **Commit:** `feat(audit): probe cli, detect, contract, CLI references`.

### S6 — Live and multi-harness (row 7)
**Do:** `skills/derail/references/runners/herdr.md` following `herdr-conductor`'s rules (never poll, one command one reply, never the own pane, file-based reports, scenario `approvals:`). One real live round of the seeded-skill scenario in a new herdr tab with a Claude worker; read the record by trace-ladder source 1 if U6 supplies a path, else scrollback `recent-unwrapped`; collect, normalize, read. `normalize` adapters: Codex only for a format actually observed (a one-prompt `codex exec --json` capture, or an existing rollout file); **agy is never launched** (M0 E5: its PATH wrapper rotates accounts on every launch), so its adapter reads the conductor-documented screen format and ships `documented only`; `harnesses/{claude,codex,agy}.md` as dated observations including what `Ctrl+O` really does where it was observed (U7). `eval` runner only if U13 passed.
**Proof:** the herdr command sequence as run (no `agent read` loops, a single background `agent wait`), the normalized `trace.md` head, `env.json`, and the closed-tab confirmation; for each adapter either a normalized sample or an `UNVERIFIED` row with the reason.
**If it fails:** the live runner ships as `documented only` with the failure recorded; headless remains the verified path. **Commit:** `feat(runners): herdr live round, harness notes, adapters (observed only)`.

### S7 — MCP (row 6) — *content batches B, C, D run in parallel with S7 code*
**Do**
1. Subagent **batches B, C, D** (§5) migrate MCP rules, security/ops and decision/`fresh/` content.
2. Main thread: `probe mcp` (stdio JSON-RPC + unauthenticated Streamable HTTP; routes to `mcpc`/Inspector when installed for authenticated servers), `scan mcp` (ecosystem table: `registerTool`, `server.tool(`, `@mcp.tool`, `#[tool]`, `AddTool`), `probe mcp --budget` (chars/4 labelled heuristic, thresholds 400/2000/4000/20 as defaults), `skills/design/` (12-question interview verbatim), audit MCP path.
3. Fixture `fixtures/mcp/seeded-server.py` (stdlib, ~10 planted defects: 40 near-duplicate tools, 9-param nested schema, unsafe tool name, stdout pollution on stdio, no annotations on a destructive tool, a 50 KB response, error returned as success text, and so on) plus a clean twin.
4. Run `/agentic-maker:audit` on it; run the old `audit-mcp-server.sh` and `measure-context-budget.sh` for comparison; derail one MCP scenario headless with `--mcp-config --strict-mcp-config`.
**Proof:** `probe mcp --budget` totals vs a hand count of the fixture's `tools/list` (`jq` on the raw response); defects found per planted list; clean twin has zero high findings; the derail run's wrong-tool (M7) or response-misread (O7) finding with verified quotes.
**If it fails:** authenticated HTTP stays `documented only` with the `mcpc` route; stdio and unauthenticated HTTP must be real. **Commit:** `feat(mcp): probe, scan, design skill, MCP references`.

### S8 — Hardening and self-audit (row 8, first half)
**Do:** `evals/` (trigger positives, negatives, seeded-defect audit cases) run with `claude plugin eval` if U10/U13 allow; `eval-emit`; footprint via `claude plugin details agentic-maker` (projected token cost) against the ≲400-token always-on target; `/agentic-maker:audit` and `/agentic-maker:derail` **on the plugin itself** (dogfood: its two knowledge skills and its own CLI as a `cli` target); README with the status table (A7), install, flows, degrade matrix; `AGENTS.md` maintainer rules (version bump in both manifests, no manual path fields, provenance markers, fixtures re-recorded only after reading the diff); CI workflow.
**Proof:** `claude plugin validate . --strict` output; `plugin details` numbers; the self-audit report with its findings fixed or recorded; `evals` results with the baseline Δ (or `UNVERIFIED` + why); CI file passes `check.sh` locally on both Pythons.
**If it fails:** an over-budget footprint means shortening descriptions, not removing the skill. **Commit:** `feat: evals, self-audit, README, CI`.

### S9 — Parity and retirement evidence (row 8, second half)
**Do:** run `scripts/parity.py` over the three source skills (A4): heading coverage 100% (each destination section carries a provenance marker; each D has a reason), table-key coverage, token-survival report with every miss restored or explained; commit `docs/parity/{ledger.tsv,REPORT.md}`. Fixture recall old vs new (A6). Derailment parity: reproduce one known derailment of the old method and demonstrate one T1 the old Modes A/C could not see (from S4). Three-project walkthrough (§9 of the design) in fresh sessions on a Rust CLI, a Python/TS MCP server and a bash+skills mixed repo — small throwaway fixtures under `fixtures/projects/`, each run to the point where the first-break items in §9 are either handled or recorded.
**Proof:** `parity.py` exit 0 and its summary line; the recall table; the walkthrough notes with the first break found on each project and what handled it.
**If it fails:** an unmapped heading is restored or gets a D with a reason, never ignored. Retirement stays the user's call: the report ends with the deletion-gate checklist (§11 of the design) marked row by row. **Commit:** `docs(parity): mechanical ledger, recall comparison, walkthrough`.

### S10 — Publish (row 9)
**Do**
1. **Pre-publish gate (all must pass):** `scripts/check.sh` full on both Pythons; secret/personal-path/email scan across the *whole tree and history* (`git log -p` grep); no file > 1 MB; every README claim has a status-table row; `claude plugin validate . --strict`; an independent `sonnet-xhigh` review of the final tree for leaks and unbacked claims; Codex `adversarial-review` of the tree if a base can be formed (otherwise noted as skipped).
2. `gh repo create yigitkonur/plugin-agentic-maker --public --source=. --remote=origin --push --description "…"`; topics (`claude-code`, `claude-code-plugin`, `mcp`, `cli`, `agent-tools`, `skills`); tag `v0.1.0` and a GitHub release whose notes list the status table.
3. **Fresh-eyes verification:** clone from GitHub into an empty dir; `claude plugin validate`; with a throwaway `CLAUDE_CONFIG_DIR` (auth behavior per U1) add the marketplace from `yigitkonur/plugin-agentic-maker`, install, list components, and run one skill via `claude -p`; run `bin/agentic-maker doctor` from the clone; run the three-line smoke from the README verbatim.
**Proof:** `gh repo view yigitkonur/plugin-agentic-maker --json visibility,url,pushedAt`; the clone path and `git rev-parse HEAD` equal the local HEAD; the install and smoke output; the release URL.
**If it fails:** the repo stays public only if the pre-publish gate passed; a fresh-clone failure is fixed with a patch release, and the failing output is shown in the report. **Commit:** `chore(release): v0.1.0`.

---

## 4. M0 spike — the sixteen experiments

Run in `<scratch>/spike/` with a throwaway plugin (`spike`) containing one DMI skill, one model-invocable skill, one `user-invocable:false` skill, one agent, and a hook-printing script. Each experiment's `system/init` event (tools, skills, plugins, MCP servers, slash commands) is saved; it is also the source of `env.json`.

| U | Experiment (what is run) | Decides |
|---|---|---|
| U1 | `claude -p` with candidate isolation: temp `CLAUDE_CONFIG_DIR` (does login survive?), `--setting-sources`, `--strict-mcp-config`, `--disable-slash-commands`; read what `init` still lists | Q4 default for CLI/MCP targets |
| U2 | `--plugin-dir` + `--add-dir` skill listing with and without `--bare` | skill-target runner |
| U3 | main-thread `stream-json` with thinking on: do `thinking` blocks appear? | `belief_source: observed` vs `inferred` |
| U4 | `hooks:` in a plugin skill's frontmatter: registered? `${CLAUDE_PLUGIN_ROOT}` set? visible in `/hooks`? | A8 placement |
| U5 | `` !`cmd` `` and `$ARGUMENTS` in a user-invoked DMI skill via `claude -p "/spike:x arg"`; failing `!cmd` | skill authoring style |
| U6 | `herdr agent get` / `agent explain` on a started worker; where `claude`/`codex` store transcripts; where `agy` stores them (`find` after one run) | trace source 1 for live runs |
| U7 | `Ctrl+O` per harness via `send-keys` on a *worker* pane, then `agent read` | `harnesses/*.md` |
| U8 | `herdr --help` trees + real JSON shapes from a tab create/close | stale-JSON-path check |
| U9 | `claude --bg`, `claude agents --json`, attach | no-herdr live runner |
| U10 | `claude plugin eval --help`; one minimal suite | `eval-emit`, own evals |
| U11 | agent `skills: [x]` where `x` is `user-invocable:false` in a plugin | reader design |
| U12 | `claude plugin details spike` projected cost; compare with description lengths | footprint budget |
| U13 | `claude plugin eval … --keep-temp`: is a readable session transcript left, with path and format? | `eval` runner = clean room |
| U14 | skill names in `init` under `--plugin-dir` vs after a local-marketplace install | validity of T1–T3 |
| U15 | a `Stop` hook that dumps stdin JSON while a background task runs: `background_tasks`, stable `session_id` | H2 false-block paths |
| U16 | a child `claude -p` launched from inside this session: env vars it inherits, whether user-level hooks fire, its `session_id` vs the parent's | H2 isolation, contamination |

---

## 5. Delegation plan (subagents get facts, not this file)

Subagents do not read `CLAUDE.md`, so each brief carries: the migration brief (S2), the target path, the destination file list, the provenance-marker format, the `fresh/` rule, and the Appendix-B resolutions that touch its sources. Each returns **raw output and paths only**: files written, headings it could not place. The main thread then runs `parity.py`, the size check and the link check, and reads a sample. A batch that returns "here's what's left" gets one follow-up subagent at most, then it is the main thread's.

| Batch | Sources (all read from `<scratch>/src/`) | Destinations |
|---|---|---|
| **A** | `audit-agentic-cli`: SKILL.md sections, `output-contracts`, `execution-patterns`, `discovery-and-auth`, `agent-integration`, `iterative-cli`, `examples`, `mcp-vs-cli-decision` | `skills/agent-interface-design/references/cli/*`, `frameworks/*`, `decisions/surface-choice.md` |
| **B** | `audit-agentic-mcp`: `tool-design`, `tool-descriptions`, `schema-design`, `tool-responses`, `error-handling`, `prompt-gates`, `agentic-patterns`, `progressive-discovery`, `context-engineering`, `caching-economics`, `tool-count` | `references/mcp/*` (design + budget) |
| **C** | `session-and-state`, `transport-and-ops`, `deployment-platforms`, `composition`, `testing`, `resources-and-prompts`, `advanced-protocol`, `security`, `threat-catalog`, `auth-identity` | `references/mcp/ops-*`, `security/*` |
| **D** | the nine decision trees, `client-compatibility`, `model-behavior`, `registry-and-distribution`, `exemplar-servers`, the dated parts of `mcp-vs-cli` | `references/decisions/*`, `references/fresh/*` (each with `as_of`) |

The **derailment** sources (`audit-skill-by-derailment`) are migrated by the main thread in S4 because they are the novel, central part. Two independent review subagents run late: `sonnet-xhigh` on CLI/probe safety (S5/S7) and on the pre-publish tree (S10).

---

## 6. Risk branches (what changes if an unknown comes back wrong)

| If… | Then |
|---|---|
| U4 fails (skill-scoped hooks inert in plugin skills) | H2 moves to `hooks/hooks.json`; same script, same early exit |
| U13 fails (no readable transcript from `plugin eval`) | `eval` runner is trigger statistics only; forensics stay on `headless` |
| U1 finds no subscription-compatible clean room | CLI/MCP targets run `in-situ` with a contamination report; docs say so |
| U3 shows no thinking text | every finding is `belief_source: inferred`; no change in the loop |
| U14 shows `--plugin-dir` names differ from an install | T-results are validated against an installed local-marketplace copy once per target |
| U6/U7 unobservable for a harness | that adapter ships `documented only`; scrollback ladder is the only source |
| U11 fails (preload of a `user-invocable:false` skill) | `trace-reader` embeds the method's invariants in its own prompt; the references are read on demand |
| `claude plugin eval` unusable | `eval-emit` and the `eval` runner are cut from v0.1 |
| A probe executes something undeclared | stop the line; fix; add the sentinel test; only then proceed |
| Estimated spend reaches USD 25 | stop and report; the user decides |

---

## 7. Publish gate (S10, copied here so it is not forgotten)

Public means indexed and cached, so the gate is checked before `gh repo create`, not after: (1) `check.sh` green on Python 3.9 and 3.14; (2) `claude plugin validate . --strict` clean; (3) zero hits for home-directory paths, personal email addresses, token prefixes and `.env` files (patterns live in `scripts/check.sh`) in the tree **and** in `git log -p`; (4) no run directories, traces or raw stream dumps committed; (5) README status table matches the ledger; (6) independent review done; (7) the version in `plugin.json` equals `marketplace.json`; (8) the three source skills untouched. After the push: fresh-clone verification (S10.3). The report to the user lists what is `UNVERIFIED`, the adopted defaults (A9, A10), and that deleting the originals is their decision, with the gate checklist from S9.

---

## 8. Ledger-to-step map

| Row | Step(s) | Evidence kept in |
|---|---|---|
| 0 Goal | all | final report |
| 1 Meta plan | this file | `docs/design/09-…` and `docs/design/09-…` |
| 2 M0 spike | S1 | `docs/what-is-true.md` |
| 3 Skeleton + CLI v1 | S0, S3 | `scripts/check.sh` output, run dir |
| 4 Derail loop | S4 | `fixtures/skills/seeded-skill`, run dir, git diff of the fix |
| 5 Audit CLI | S5 | probe output, sentinel check |
| 6 Audit MCP | S7 | probe output, hand count |
| 7 Live herdr | S6 | command sequence, `trace.md` |
| 8 Parity, self-audit | S8, S9 | `docs/parity/`, `plugin details` |
| 9 Publish | S10 | `gh repo view`, fresh-clone output |

The task list mirrors this table one-to-one; after any compaction the first move is to re-post row 0 and the open rows.
