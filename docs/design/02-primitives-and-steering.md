> Part of the `agentic-maker` plan · [README](README.md)

## 4. What Claude Code natively provides today (docs read 2026-10-20) and the decision for each

| Primitive | Facts that matter here | Decision |
|---|---|---|
| **Skills** (`skills/<n>/SKILL.md`) | Namespaced `/plugin:skill`. `disable-model-invocation: true` ⇒ description **not in context**, but the skill also **cannot be preloaded into subagents**. `user-invocable: false` hides from menu. `context: fork` + `agent:` runs in a subagent. `!`cmd`` injects command output pre-prompt. `allowed-tools`, `hooks:` in frontmatter (registered on invocation, live for the session), `paths:`, `${CLAUDE_SKILL_DIR}`, `$ARGUMENTS`. Description+`when_to_use` capped at 1,536 chars in the listing. **Gotchas verified:** a failing `!`cmd`` (non-zero exit, or a command the permission check doesn't *allow*) **aborts the entire invocation** → always `|| true` and keep injected commands read-only and pre-approvable; `context: fork` = no conversation history, no `AskUserQuestion`, background by default (`background: false` to wait); an `allowed-tools` grant **clears at the user's next message** (long loops need a documented `permissions.allow` rule for `Bash(agentic-maker *)`). | **Use heavily.** Procedures = DMI user-invoked skills (zero context cost until typed). Two knowledge skills model-invocable. Skill-scoped hook for the loop guard. |
| **Subagents** (`agents/*.md`) | Own context. Plugin agents honor `model,effort,tools,disallowedTools,skills,memory,isolation,maxTurns…`; **ignore `hooks, mcpServers, permissionMode, initialPrompt`**. `tools` is a name list — it **cannot restrict `Write` to a path**. `skills:` preloads. Subagents may nest up to 3 layers (not needed here). | **One agent**: `trace-reader`, tools `Read, Grep, Glob` **only**, returns findings as JSON in its final message. |
| **Hooks** (5 handler types; ~30 events) | Plugin `hooks/hooks.json` fire in every session where the plugin is enabled; matchers per event; `SubagentStop` can block with `reason`; `Stop` has `stop_hook_active`; `additionalContext` capped 10k chars. | **Strict bar** (§5): ≤2 kept, both silent unless a derail run is active. |
| **`bin/`** | On the **Bash tool's** PATH while enabled — not documented for hook processes (hooks use `${CLAUDE_PLUGIN_ROOT}/bin/…`). claude.ai/Cowork won't install a plugin with a top-level `bin/` (fine: Claude Code only). | **Use**: the `agentic-maker` CLI. |
| **MCP servers** (`.mcp.json`) | Tool descriptions load per session. | **Reject** for v1 (ironic cost; our ops are file-in/file-out; CLI is cheaper and testable). |
| **Monitors** | Background process whose output notifies Claude. | **Reject** (herdr `agent wait` is the sanctioned non-polling wait). |
| **Workflows** (`workflows/*.js`) | Plugin workflows run as `/plugin:name`; many subagents; user-started = opt-in. | **Later** (M5): `/agentic-maker:derail-matrix` for fleets (≥6 parallel readers). |
| **Plugin `settings.json`** | Only `agent` and `subagentStatusLine` take effect. | **Reject** (`agent` would hijack the session). |
| **`userConfig`** | Install-time dialog. | **Reject** (zero-config; optional `.agentic-maker/config.md` like swiftui's settings file). |
| **Output styles / themes / LSP / channels / mods** | Mods = in-process JS, CC-only, bigger trust surface. | **Reject** (nothing here needs UI; mods would break cross-harness stance). |
| **Plugin dependencies** | Hard-installs another plugin. | **Soft only** for `herdr-conductor` (README + `doctor`); a hard dep forces herdr on everyone. |
| **`claude plugin validate` / `eval` / `tag`** | validate in CI. eval = N isolated `claude -p` runs with only the plugin loaded (temp home/config, allowlisted env, OS sandbox), `tool_used`/regex/file/llm graders, no-plugin baseline Δ, `--keep-temp`, `--max-cost-usd`, `--json`. | **Use** validate. eval is both our own trigger-regression tool **and a candidate clean-room runner** for skill/plugin targets (§6.2, U13). |
| **Headless** (`-p --output-format stream-json --verbose --include-hook-events --session-id --max-turns --max-budget-usd --plugin-dir --mcp-config --strict-mcp-config --permission-mode --allowedTools`) | Structured, documented event stream; `--bare` needs API-key auth. `--bg` background sessions exist (`claude agents --json`, `claude attach`). | **Primary cheap runner.** `--bg` evaluated in M0 as a no-herdr live runner. |

---

## 5. Steering strategy — where each piece of knowledge goes and when it arrives

**Principle:** the agent should receive each thing *at the moment it prevents a failure*, from the cheapest vehicle that works. Always-on cost is the enemy (the plugin is itself an agent-facing surface and must pass its own audit).

| Knowledge / workflow | Vehicle | Arrives when | Why not another vehicle |
|---|---|---|---|
| Procedures: audit, design, derail | **User-invoked skills** (`disable-model-invocation: true`) | The user types `/agentic-maker:…` | They spend money / spawn agents / edit files; explicit opt-in; descriptions cost 0 tokens |
| Surface-neutral design contract + routing to deep refs | **Model-invocable skill `agent-interface-design`** | The agent is *writing or reviewing* a CLI/script/MCP tool/skill meant for agents ("my agent keeps failing to parse…", "tool descriptions", "exit codes") | This is write-time steering; waiting for a command is too late. Description ≤ ~400 chars; negative cases in evals |
| Derailment method (invariants, taxonomy, fix patterns, reading playbook) | **Skill `derailment-method`** (`user-invocable: false`, model-invocable, narrow) | (a) preloaded into `trace-reader` via `skills:`; (b) pulled by the main agent when diagnosing "why did my agent skip/guess" | Must not be DMI (DMI blocks preload). Narrow description keeps it off unrelated turns |
| Long traces | **Subagent `trace-reader`** | `/agentic-maker:derail` step "read" (parallel, ≤5) | Raw traces are 10–100× larger than findings; isolated context returns a findings JSON (saved by the orchestrator per run) |
| Deep references (per surface, per framework, dated facts) | **Files read on demand** from the owning skill's `references/` | A router table says "read X when Y" | Progressive disclosure; each ≤ ~8 KB, one decision |
| Measurement (is JSON pure? what's the real token budget?) | **`agentic-maker` CLI** (`bin/`), envelope with `next_actions` | Run by the skill/agent; output tells the next step | Replaces regex-over-source with runtime facts; zero context cost until run |
| Run state (round, findings, receipts, what changed since last trace) | **Files** in `.agentic-maker/runs/<id>/` + ledger | Read after compaction / by hooks | Survives compaction; the filesystem is the only channel between subagents |

### Hooks — kept (1), conditional (2), rejected (10)

Bar: a hook must prevent a failure that has actually been observed (here or in the sources), at the exact moment, silently otherwise (<10 ms exit when no run is active), deterministically, and without ever trapping the agent.

**KEPT (1) — H2, `Stop` gate while a derail run is active → `${CLAUDE_PLUGIN_ROOT}/bin/agentic-maker ledger gate`.** Prevents the orchestrator's own *premature completion illusion (C1)* — "fixed" claimed after editing the target but before a fresh trace shows it. Observed class: C1 is the taxonomy's top cognitive failure in *workers*, and the user's own global rules and swiftui's fix-safety #8 ("a claim of 'fixed' with no fresh evidence is not done") exist because it recurs in orchestrators. Orchestrator-level recurrence is to be **confirmed in M1 dogfooding; ship with a kill switch and delete if never seen.** Hardening (from the adversarial review — each is a real false-block path):
- Ledger and pointer are keyed to the **orchestrator's `session_id`**; any other session (including an in-situ worker) exits 0 immediately.
- **Pass** (never block) when: `stop_hook_active`; `background_tasks` non-empty (a rerun/wait is in flight); ledger status `awaiting_user`, `closed`, or `unverified-recorded`; budget spent; TTL (6 h) expired; the run was abandoned (`ledger abandon`).
- Block only on: target files modified after the newest *completed* trace **and** status `fixing`. The reason names the files and offers exactly three exits: rerun scenario X, record UNVERIFIED with a reason, or abandon.
- Registered in `derail/SKILL.md` frontmatter (`hooks:`) so sessions that never run `/agentic-maker:derail` pay nothing; the command uses `${CLAUDE_PLUGIN_ROOT}` (hook processes don't get the Bash-tool PATH). *Verified in M0 (U4, U15):* skill-scoped hooks fire from a plugin skill, `${CLAUDE_PLUGIN_ROOT}` expands in their commands, the `Stop` payload carries `session_id`, `stop_hook_active`, `background_tasks` and `transcript_path`, so no `hooks/hooks.json` is shipped.

**CONDITIONAL (2)**
- **H1 `SubagentStop` matcher `^agentic-maker:trace-reader$` → verify the reader's final JSON.** Not needed in v1: the same protection is **structural** — the reader has `Read, Grep, Glob` only and returns JSON; the orchestrator must pass it through `agentic-maker check findings` (quotes verbatim in the cited trace events, required fields, valid codes) before any finding can be recorded by `ledger fix`; an unverified edit still trips H2 because the target is newer than the trace. Add H1 only if dogfooding shows the orchestrator skipping `check`. Caveats found in review: hook only sees `agent_id` (parallel readers need per-reader output paths), a hard 8-continuation cap, and `last_assistant_message` isn't the report when `SubagentHandback` is used.
- **H3 `SessionStart` (`compact|resume`) → re-post run ledger summary** (run id, round, open findings, last trace path; note that background waiters are gone after resume). Ship only if dogfooding shows loop state is lost after compaction; otherwise the ledger file + a "read the ledger" line suffices.

**REJECTED (and why)**
1. `SessionStart` on `startup` context injection — noise in every session; all entry points are explicit commands.
2. `UserPromptSubmit` router — duplicates description matching; per-prompt latency; wrong-fires.
3. `PostToolUse` nudge on edits to `SKILL.md`/tool descriptions (the swiftui pattern) — swiftui's works because deprecated names are a closed word list; "this edit appended a rule instead of fixing the cause" is semantic. The `check diff` gate (§6.7) judges the *applied* diff where evidence exists.
4. `PreToolUse` guard around probing the audited CLI — we can't know which subcommands are destructive; `agentic-maker probe` is allowlist-by-construction (only declared read-only commands + help/version) and the permission system already prompts. (Review caveat: `--help` on a shebang script that ignores its arguments *runs* the script — scripts get a static read of their argument handling first, and probes run in a temp cwd with a timeout.)
5. `PreToolUse` own-pane protection — `herdr-conductor` already ships it; duplicating = two sources of truth.
6. `prompt`/`agent`-type hook judging each fix — per-edit cost, non-deterministic; the **rerun** is the real test.
7. `FileChanged`/monitor for live-run progress — polling by another name; herdr waits are the sanctioned mechanism.
8. `PermissionRequest` auto-allow — `allowed-tools: Bash(agentic-maker *)` in frontmatter does it declaratively for the turn; because that grant **clears at the user's next message**, long loops are covered by a documented one-line `permissions.allow` rule, not a hook.
9. `PreCompact` — can't inject; the seam is H3.
10. In-process **mods** — CC-only, heavier trust surface, nothing to draw.

**Context-cost budget:** always-on = descriptions of `agent-interface-design`, `derailment-method`, `trace-reader` (target ≲ 400 tokens, measured with `/plugin` context cost per docs/plugins/measure). Acceptance: the plugin audits itself clean.

---


---
### Claims to verify (M0)
- U4 resolved in M0 (see [what-is-true](../what-is-true.md)); still unchecked: visibility of the hook in `/hooks` (interactive only).
- U5 `!`cmd`` / `$ARGUMENTS` / `allowed-tools` behavior in user-invoked skills.
- U11 `skills:` preload of a `user-invocable: false` skill into a plugin agent.
- U12 measured always-on footprint (3 descriptions) against the ≲400-token budget.
- U15 `Stop` hook input: `background_tasks` populated during a rerun; stable `session_id`.
