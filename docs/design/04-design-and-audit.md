> Part of the `agentic-maker` plan · [README](README.md)

## 7. The design/audit side

**Surface-neutral contract** (the new front door; `agent-interface-design/references/contract.md`) — eight questions that cover CLI, script, MCP, skill:
1. **Intent** — built around what the agent is trying to do, not endpoints/internals? 2. **Contract** — inputs/outputs/errors machine-checkable (stdout=data; `isError`; typed, flat, ≤6 required)? 3. **Discovery** — can an agent learn it from the surface itself (help/description/`instructions`/examples), cold? 4. **Steering** — does each response say what to do next (`next_actions`/`guidance`, bounded, disclosed)? 5. **Safety** — destructive ops explicit (`--dry-run/--yes`, annotations, guards scaled to stakes), secrets off argv, untrusted-text handling? 6. **Budget** — definition + response tokens proportionate (≤20 active tools, response caps, concise/detailed)? 7. **Recovery** — errors teach (field, expected, recovery call with real values, retry cap, loop breaker)? 8. **Verification** — can it be exercised live and non-interactively (never hangs)? Each question has the CLI-flavoured and MCP-flavoured answer in the surface references; the 5 CLI checks and 15 MCP hard rules are *instances* of these.

**`/agentic-maker:audit [target]`** (`context: fork`, `background: false`; **audit stops at a report**, as in the old MCP rule 2; fixes are a separate "apply F1–F4" turn in the main thread, verified by re-running the same probe). A fork has no conversation history and no `AskUserQuestion`, so the target must be in the arguments and ambiguity is handled by **asking-by-returning** (the fork returns the inventory + "re-run with a target"). Injected commands are read-only and end `|| true` (a failing `!`cmd`` would abort the whole invocation):
1. `!`agentic-maker detect --brief || true`` injected (M2+; data-driven `surfaces.tsv`: kind, detect signals by ecosystem, probe, rubric, exposure recipe — until then the user names the target). One surface at a time. Tool-registration signals include `registerTool`, `server.tool(`, `@mcp.tool`, `#[tool]` (rmcp), `AddTool` (Go) — the old regex's coverage, extended per ecosystem.
2. **Runtime probes first, static scan only to locate:**
   - `agentic-maker probe cli <bin> [--safe-cmds file]` (M2) — help/version capture + standard-flag/examples/exit-code-doc scan (old script) **plus** executed checks on *declared* read-only commands: stdout parses as JSON, stderr separate, exit-code map on declared failure cases, no-TTY/closed-stdin hang test with timeout, `NO_COLOR`. Safety: only declared commands + help/version; run in a temp cwd, timeout, no network where the platform allows; a shebang script gets a **static read of its argument handling first** (a script that ignores `--help` would just run). Compiled targets need `build:`/`bin:` (a crate name isn't a path). (The old script explicitly could not prove agent-readiness.)
   - `agentic-maker probe mcp <cmd|url|config>` (M4) — connects, `tools/list`: count, per-tool description/schema chars, depth, required-param count, annotations, name regex `^[a-z][a-z0-9_]{0,63}$`, duplicate/near-duplicate descriptions, stdout pollution on stdio, `instructions`, capabilities; budget = chars/4 **labelled heuristic**, old thresholds (400/2000/4000/20) as defaults. Works for a Rust/Go/Python/TS server alike — this is what makes it language-agnostic. Scope honesty: a stdlib JSON-RPC/HTTP/OAuth client is real work — v1 supports stdio + unauthenticated Streamable HTTP, and **routes to `mcpc`/MCP Inspector CLI when installed** for authenticated servers (the old skill already did); servers needing a build or secrets fall back to `scan mcp` (regex, locate-only) or a user-supplied `tools/list` capture.
3. Apply the rubric for the detected kind; every finding cites path:line or probe output, or is a labeled assumption; severity in agent terms (Critical/High/Medium/Low); scorecard dimensions kept (tool interface, schemas/responses, errors, security/auth, context/cost, client compatibility, ops/testing, architecture; CLI: the five checks + finish criteria).
4. Output contract kept (scorecard, prioritized findings with evidence+impact+fix+verification, assumptions/not touched).

**`/agentic-maker:design <idea>`** (main thread, interactive): the 12-question interview *verbatim*, surface-choice decision (`decisions/surface-choice.md`: CLI default when a mature CLI exists; MCP only for per-user auth/tenancy/approvals/typed remote discovery/shared multi-client/state; skill when the gap is workflow guidance; hybrid control-plane/execution-plane; label every recommendation *documented fact / benchmark / practitioner report*), framework/companion routing (optional; only names companions if installed), architecture-sketch template, CLI refactor-contract / iterative-repair-design deliverables, approval before any code.

**Freshness mechanism:** every time-sensitive reference lives in `references/fresh/` with `as_of:` frontmatter; `agentic-maker doctor` lists items older than a threshold (M5); the README describes re-verification (can use the `research` plugin when installed). We never *claim* currency; the SKILL says "verify before citing" exactly where the old one did.

---


## 9. Staying language- and project-agnostic

- **Black-box first:** probes act on the public interface (an executable, an MCP endpoint, a skill's text), so Rust/Go/Python/TS/bash targets behave identically. Static scanning is a locate-only fallback driven by `surfaces.tsv` (Cargo `[[bin]]`/clap, `package.json bin`, `[project.scripts]`, cobra/`main`, shebang scripts; MCP: TS SDK, FastMCP, rmcp, mcp-go).
- **Framework advice isolated** in `frameworks/<stack>.md` (old Go/Cobra/Python/Node/Rust/Bash example code is split here, never in core).
- **Degrade, never break:** missing `python3` ⇒ skills still work as text and `doctor` says what's lost; missing `herdr` ⇒ headless only; missing `rg`/`jq` ⇒ grep/python; no API key ⇒ in-situ + contamination report; no `claude plugin eval` ⇒ skip `eval-emit`.
- **Three-project test (acceptance):**

| Project | Detect → Audit | Derail |
|---|---|---|
| **A. Rust CLI (clap)** | `surfaces.tsv` → cli-rust; `probe cli` executes `--json` on declared read-only commands, finds stderr/stdout mix + `exit 1` for all errors; rubric + `frameworks/rust-clap.md`. **First break:** no binary path (`target/debug/<bin>` ≠ crate name) and, cold, an empty `--safe-cmds` ⇒ only help/version probed → scenario `build:`/`bin:` fields; `audit` says plainly what was *not* executed | headless, cold (`--help` only); finds M7/O7/C5 (e.g. agent re-runs after misreading a table as success); fix = rewrite error message/exit codes; rerun |
| **B. Python FastMCP (or TS/Go) server** | cli not applicable; `probe mcp` lists real tools → budget, depth, name regex, missing annotations; hard rules + `fresh/` client matrix flagged "verify". **First break:** Go/TS servers need a build and env secrets before `tools/list` works → `build:`/`env:`, else `scan mcp` or a user-supplied `tools/list` capture; authenticated HTTP → route to `mcpc`/Inspector | `--mcp-config --strict-mcp-config`; finds wrong-tool picks (M7), arg errors, 40k-token responses (O8); fix = description/response rewrite; rerun |
| **C. Bash script + `skills/` mixed repo** | detects skill + script; skill read as text, script probed like a CLI. **First breaks:** `--help` on a script that ignores args *runs it* (static read first); relative script paths break in the temp cwd (fixtures copy the repo subset) | skill target: prompt never names it ⇒ T1/T2; references never read ⇒ S4; fix = routing row/description; confirming live herdr round; `eval-emit`. **Naming caveat:** `--plugin-dir` skill names can differ from an install's `<plugin>:<skill>` (U14) — recorded in `env.json` |

---


---
### Claims to verify
- `audit` as a `context: fork` skill: injected `!` commands end `|| true`; ask-by-returning works as described (U5).
- `probe cli`/`probe mcp` safety and scope claims are validated in M2/M4 against the seeded fixtures, not assumed.
