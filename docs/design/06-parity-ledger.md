> Part of the `agentic-maker` plan · [README](README.md)

## 10. Parity — where every important idea lands (nothing silently dropped)

Legend: **K** = kept (reworded/split), **M** = merged, **R** = replaced by a native mechanism, **D** = dropped by decision (reason). The tables below are file-level. The **row-level ledger is generated mechanically from the source files themselves, not from my summaries** (the Haiku inventories were useful for reading but five were truncated): a script lists every H1–H3 heading and every bullet/table row of every source file; each gets a destination or a D with a reason; **a deterministic coverage check fails if any source heading is missing from the ledger.** That check is deletion-gate item 1 (§11).

**Honest note on repackaging:** the references (rubrics, hard rules, decision trees, fix patterns) are *content*, and content is what has value — those are carried, split to ≤8 KB single-decision files with the Appendix B defects fixed. What is redesigned is the *vehicle* (which primitive, which arrival moment), the *evidence* (runtime probes, trace ladder, verified findings, receipts), the *runners*, and the *loop discipline*.

Two items the first draft lost, now recorded: (a) CLI SKILL.md's **"fix the CLI before blaming the architecture"** rule → `decisions/surface-choice.md` + `cli/checks.md` (explicit rule row, kept verbatim in spirit); (b) the old **Mode A cheap in-session run** → **D**: it shares the parent's skills/CLAUDE.md so it isn't a fresh session; replaced by `--runner headless --max-turns 8`.

### 10.1 audit-agentic-cli
| Source | Destination |
|---|---|
| SKILL.md: 5 core checks, severity rubric, envelope, build order (6), audit workflow (8), iterative loop, design rules, 3 deliverable shapes, finish criteria, exemplars | K → `cli/checks.md` (checks+severity+finish), `audit/` (workflow+report), `design/` (deliverables), **R** → `probe cli` executes checks 1–5. Exemplars `linear-cli`/`run-railway` D (author-local) → pointer in `decisions/companion-routing.md` |
| `output-contracts.md` (envelopes, schemas, exit codes 0–8, classes, JSONL, field selection, pagination, quiet, stream separation) | K, split → `cli/output-contracts.md`, `exit-codes.md` (**one reconciled table**, Q-decision), `streams-and-jsonl.md`; Appendix B fixes |
| `execution-patterns.md` (idempotency, retry, dry-run, non-interactive, batch/partial, rollback, async, timeouts/signals, pagination, rate limit, continuation modes) | K, split into 6 files under `cli/`; continuation modes → also `decisions/steering-contract.md` |
| `discovery-and-auth.md` (flags matrix, config precedence, auth flows, grammar, help-answers-5-questions, version/capabilities, secrets, env detection) | K → `cli/discovery-and-help.md`, `auth-and-secrets.md`, `config-and-env.md` |
| `agent-integration.md` (caller wrappers, retry/circuit-breaker, recovery, framework bindings, observability, steering §16–17) | K (language-neutral) + code → `frameworks/`; observability trimmed to the CLI-facing parts; steering → `decisions/steering-contract.md` |
| `iterative-cli.md` | K → `cli/iterative-repair.md` (+ `design` deliverable) |
| `mcp-vs-cli-decision.md` | M with MCP `mcp-vs-cli.md` → `decisions/surface-choice.md`; dated benchmark/Reddit → `fresh/` |
| `examples.md` (Go/Python/Node/Rust/Bash, gh/kubectl/aws audits, tests) | K → `frameworks/*`, `cli/case-studies.md` (audit scores flagged *unverified vs current versions*; rubric formalized in `audit/references/scoring.md`) |
| `scripts/audit-cli-help.sh`, `diff-cli-help.sh` | R/K → `probe cli` (help scan retained) and `probe cli-diff` |
| `agents/openai.yaml` (no implicit invocation) | R → `disable-model-invocation: true` |

### 10.2 audit-agentic-mcp
| Source | Destination |
|---|---|
| SKILL.md: 15 hard rules, 2 modes, output contracts, minimal read sets, execution rhythm, decision tree, quick reference, 10 pitfalls, freshness list, companion table, delegation policy | K → `mcp/hard-rules.md`, `audit/`, `design/`, SKILL routing table, `fresh/` mechanism; companion table → optional `decisions/companion-routing.md`; delegation policy D (user-level policy, not plugin) |
| 9 decision trees (brainstorming, companion-toolchain, design-phase, error-strategy, production-readiness, response-format, scaling, security-posture, tool-count) | K → `decisions/*.md` (same names); `brainstorming` = `design/references/interview.md` (12 Qs verbatim); per-model caps in tool-count marked dated |
| tool-design, tool-descriptions, schema-design, tool-responses, error-handling | K → `mcp/` core (intent tools; Verb+Resource first 5 words; coercion; flat ≤6; enums inline; safe names; response-as-prompt; concise/detailed; semantic IDs; truncation signal; YAML/TSV; annotations; structuredContent+text; isError vs protocol; teach-in-errors; loop breaker). Resolve the description-length tension explicitly (§11 B16) |
| prompt-gates, agentic-patterns | K/M → `decisions/steering-contract.md` + `mcp/steering-and-gates.md`; **the steering-vs-injection tension stated once** (steering via tool output is powerful; the same channel is the attack surface — bridge: namespaced guidance + `allowed_next_tools`) |
| progressive-discovery, context-engineering, caching-economics, tool-count | K → `mcp/budget-*.md`; **R** by `probe mcp` measurements; cache cases dated |
| session-and-state, transport-and-ops, deployment-platforms, composition, testing, resources-and-prompts, advanced-protocol | K → `mcp/ops-*.md`, `protocol-features.md`; deployment-platforms → `fresh/` |
| security, threat-catalog, auth-identity | K → `mcp/security/*` (generic defenses; 20-primitive catalog; 36-item checklist; auth profile) — CVEs/versions/scanners dated, `fresh/` |
| client-compatibility, model-behavior, registry-and-distribution, exemplar-servers, mcp-vs-cli (dated parts) | K → `fresh/` with `as_of:`; contradictions reconciled or flagged (Appendix B) |
| `audit-mcp-server.sh` | R → `scan mcp` (locate-only, ecosystem table) + `probe mcp` (runtime) |
| `measure-context-budget.sh` | R → `probe mcp --budget` (real `tools/list`; thresholds 400/2000/4000/20 preserved as defaults) |

### 10.3 audit-skill-by-derailment
| Source | Destination |
|---|---|
| 5 invariants (fix text not executor; anti-self-report; Ctrl+O; scaffold 20–30; no errata) | K → `derailment-method` invariants, **reworded**: #3 → "never judge from a view that hides the run" (trace ladder); #4 → breadth dimensions, no quota; others unchanged |
| Severity/root-cause sheet, 4 markers, P0/P1/P2, compound-P0, **21 codes**, fix-pattern matrix | K → `taxonomy.md`, `fix-patterns.md` (+ T1–T3, M7, O7, O8, C5) |
| Tri-modal routing | K → runners `headless | herdr | existing` (§6.1) |
| Mode C steps (tab, agent start, prompt, Ctrl+O, wait, auditor, patches, cleanup) | K → `runners/herdr.md` via conductor rules; callback law **replaced** (files + background wait); cleanup = close only tabs this run created |
| `herdr-native-runner.md` (workspace/tab lifecycle, start, prompt, return-address contract, wait + polling fallback, scrollback, send-keys, teardown) | K minimal; syntax deferred to `--help`/conductor; polling fallback **D** (never poll); return-address contract **R** (file-based report) |
| `ctrl-o-verbose-physics.md` | K → `harnesses/*.md` as dated observations + the trace ladder |
| `herdr-pane-audit.md` (Mode B, cognitive-model heuristics A–D, corrective prompts, cross-pattern matrix) | K → `runners/existing.md`, `reading-traces.md`, `synthesis-matrix.md`; corrective prompts only post-capture |
| `forensic-subagent-briefs.md` (two-tier, universal brief, parallel auditors, handback contract) | K → `agents/trace-reader.md` + finding schema; auditor **read-only**, orchestrator single writer; parallel ≤5 else workflow |
| `disk-evidence-and-anti-sycophancy.md` (self-report mirage, 5 gates, artifact recipe) | K → `evidence-and-anti-sycophancy.md` + `receipts` kinds (generic, not media) |
| `friction-taxonomy-guide.md`, `fix-patterns.md` | K (above) |
| Scripts: `launch-derailment.sh` | R → `agentic-maker run` (prompt rendering without marker instructions; `--self-annotate` optional) |
| `parse-derailment-trace.sh` | R → `agentic-maker normalize` (+ marker counting if self-annotated) |
| `audit-worker-pane.sh`, `read-herdr-panes.sh` | R → `collect`/`normalize --source herdr`, `receipts`; media/`__TAKE_RESULT_JSON` specifics **D** (domain leak) |
| `openai.yaml` | R → DMI |

---


---
### Build task, not a claim
The row-level ledger (`parity-ledger-rows.md`) is **generated mechanically from the source files** — every H1–H3 heading and bullet/table row — with a coverage check that fails if any source heading lacks a destination. That check is deletion-gate item 1 in [07](07-build-and-retire.md).
