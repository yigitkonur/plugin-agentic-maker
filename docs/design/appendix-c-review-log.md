> Part of the `agentic-maker` plan · [README](README.md)

## Appendix C — review log (adversarial pass on the first draft; every item verified against the saved docs before acting)
| Finding | Verdict | Change made |
|---|---|---|
| `disable-model-invocation` blocks subagent preload | verified | `derailment-method` is `user-invocable:false`, **not** DMI |
| Plugin agents ignore `hooks`; `tools` can't path-restrict `Write` | verified | Reader is `Read, Grep, Glob` only, returns JSON; draft's "Write→findings.json only" removed |
| `bin/` is on the Bash tool's PATH, not hook processes | verified | Hooks use `${CLAUDE_PLUGIN_ROOT}/bin/agentic-maker` |
| `--bare`: API key only **and** no skill listing | verified | `--bare` dropped as isolation; T-tests need the skill listing; `eval` runner added (temp home/config, only plugin loaded, sandbox) |
| `context: fork`: no history, no `AskUserQuestion`, background by default; failing `!`cmd`` aborts the skill | verified | `audit` = `background: false`, ask-by-returning, `|| true` on injected commands |
| `allowed-tools` grant clears at next user message | verified | Rejected-hook #8 reason corrected; `permissions.allow` rule documented |
| Subagents can nest (3 layers) | verified (my draft was wrong) | Statement removed |
| "Eval is early access" means the build predates GA | verified (my draft was wrong) | Reworded; `claude update` noted (U10) |
| Delegating to `herdr-worker` contaminates the brief; guard denies bypass flags; conductor forbids scripts driving agents | verified | Herdr runner follows conductor rules directly, scenario `approvals:`, agent-driven mechanics |
| H2 false-blocks (in-flight reruns/waits, user questions, abandoned runs, worker sessions) | accepted | Session-keyed ledger, pass conditions, TTL, `abandon`, temp-cwd workers |
| H1 attribution (parallel readers share `agent_id` handling), 8-continuation cap | accepted | H1 demoted to conditional; structural `check findings` gate |
| `patch-by-rule` weak (regex, proposals not diffs, fires on ABSENT) | accepted | `check diff` on applied diff; silent for `ABSENT`; machine-checkable `rerun_predicate`s |
| No total budget; readers outside caps; herdr uncapped | accepted | `budget_usd_total` + cost preview/confirm at FRAME |
| Unsandboxed headless worker in real HOME | accepted | Temp workspace, allowlisted tools/env, sandbox for destructive-capable targets |
| Over-scoped v1 CLI (17 subcommands); `probe mcp` is a client implementation | accepted | v1 CLI = 5 commands; `probe mcp` M4 with `mcpc`/Inspector routing; setup skill deferred |
| Milestone order | accepted | Skill-derail (`existing`+`headless`) → CLI → live → MCP |
| Three-project first-breaks (build/bin path, env secrets, `--help` runs scripts, temp-cwd paths, `--plugin-dir` naming) | accepted | Scenario `build/bin/env`; static read before probing scripts; U14 |
| Row-level ledger not earned; two rows lost | accepted | Mechanical heading-coverage gate; two rows recorded |
| Reviewer: "tool-registration regex misses `registerTool`" | **not accepted** — the old `audit-mcp-server.sh` pattern already includes `registerTool`; ecosystem table extended instead | — |
