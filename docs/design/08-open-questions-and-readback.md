> Part of the `agentic-maker` plan · [README](README.md)

## 13. Open questions (recommended default in bold)

- **Q1 Name.** **`agentic-maker`** (`/agentic-maker:audit|design|derail`). Alternatives: `agent-tooling`, `derail`.
- **Q2 Default runner.** **Headless for inner rounds (or `eval` for skill/plugin targets if U13 passes), one herdr live round to confirm**; herdr when `interactive: true`, harness is agy, or the user asks. (Alternative: herdr always — higher fidelity, slower, sequential.)
- **Q3 herdr-conductor dependency.** **Soft** (detect + recommend; defer syntax to it when present). Hard dependency rejected.
- **Q4 Isolation default.** **Skill/plugin targets: `clean` via the `eval` runner if U13 passes. CLI/MCP targets: `in-situ` with a recorded contamination report unless U1 finds a subscription-compatible recipe.** `--bare` is not used for trigger tests at all (it drops the skill listing).
- **Q5 Taxonomy extension.** **Yes: add T1–T3, M7, O7, O8, C5; original 21 IDs frozen.**
- **Q6 Time-sensitive MCP facts** (model matrix, client matrix, registries, exemplars, platform prices, CVEs, benchmarks). **Keep all, in `fresh/` with `as_of`, never cited without a re-check line; no claim of currency.** (Alternative: drop vendor/price tables — loses real signal.)
- **Q7 Companion skills** (`build-mcp-server-sdk-v1/v2`, `build-mcp-use-server`, `convert-mcp-sdk-v1-to-v2`, `test-by-mcpc-cli`, `run-railway`, `linear-cli`). **Stay separate; routed to only if installed.** `probe mcp` is the read-only inspector; `mcpc` remains the heavier live tester.
- **Q8 Exit-code table.** **Adopt 0–8 (8 = partial) as the one canonical table**; classes `usage`/`transient` added to the enum; batch response uses 8, not 3. (The sources disagree; this is a content decision, flagged for you.)
- **Q9 Platform.** **macOS/Linux/WSL, bash + python3 stdlib.** Native Windows later.
- **Q10 Codex/agy as *hosts* (dual packaging like swiftui).** **No for v1**; keep SKILL.md portable; they are supported as *workers*.
- **Q11 `claude plugin eval` integration.** **Optional `eval-emit`**; our own `evals/` for trigger/negative cases.
- **Q12 `audit` write behavior.** **Report only**; "apply F1–F4" is a second step; scenario files and reports under `.agentic-maker/` (runs gitignored).
- **Q13 Fleet matrix via `Workflow`.** **Defer to M5** as an explicit `/agentic-maker:derail-matrix`.
- **Q14 Ship order.** **Skill-derailment first (M1), CLI second (M2), MCP last (M4)** — opposite of the brief's "design first" listing, because derailment is the novel/risky half, `existing`+`headless` need no launch machinery, and the loop then tests the migrated knowledge. (Alternative: migrate design knowledge first — safer content, but nothing yet to test it with.)
- **Q15 Hook count.** **One hook (H2) with a kill switch; H1/H3 only on evidence.** (Alternative: zero hooks in v1 — defensible; H2's value is unproven at orchestrator level until M1 dogfooding.)
- **Q16 Reader tools.** **`Read, Grep, Glob` only; disk checks precomputed by `check receipts`.** (Alternative: allow `Bash` for ad-hoc checks — breaks read-only.)

---

## 14. Read-back (the four questions)

1. **Did every valuable idea make it?** At file level yes (§10 maps all 66 reference files + 8 scripts + 3 SKILL.md, and the review found two rows the first draft lost — "fix the CLI before blaming the architecture" and the cheap in-session run — now recorded). At row level it is **not claimed yet**: the row-level ledger is generated mechanically from the source files with a heading-coverage check, and passing that check is deletion-gate item 1. Ideas that *changed shape* are called out (Ctrl+O → trace ladder; callback → files; quota → dimensions; markers → reader-assigned; Mode A → headless).
2. **Does each hook earn its place?** One kept (H2, tied to the C1 failure class, hardened against the false-block paths the review found, kill-switched, to be confirmed in M1); two conditional on evidence (H1 is replaced by a structural gate; H3 only if compaction loses state); ten rejected with reasons. Zero always-on hooks.
3. **Would it hold up on three very different projects?** §9: Rust CLI, Python/TS/Go MCP server, bash+skills repo — all handled by black-box probes + scenario-driven fresh agents; language code isolated in `frameworks/`; every dependency degrades.
4. **Is anything just an old skill moved into a new folder?** The three old skills are *not* preserved as units. Redesigned: one surface-neutral contract; runtime probes replacing regex/text scans; trace ladder + normalizer replacing Ctrl+O/scrollback-grepping; reader-assigned findings with evidence verification replacing self-annotation and a 20–30 quota; trigger-layer testing (T1–T3) that the old modes couldn't see; file-based worker reports replacing callback prompts; `bin/` CLI with `next_actions` replacing 8 sidecar-documented scripts; steering placed by arrival-moment instead of by origin skill. Inherited content that *is* carried (rubrics, hard rules, decision trees, fix patterns) is split to ≤8 KB single-decision files with the 25 known defects fixed — and the plan says so plainly (§10 note): the references are repackaged content, the vehicles, evidence and loop are the redesign.
5. **Is "fix the reason, not add rules" preserved *and enforceable*?** Preserved as the central finding contract (controlling text + belief + source-rewrite). Enforced by: `check findings` (verbatim evidence before any edit), `check diff` on the **applied** diff (`patch-by-rule`, silent when the controlling text is `ABSENT`), machine-checkable `rerun_predicate`s, the `[NICE]` guard, and H2 refusing "done" without a fresh trace. Residual weakness (stated, not hidden): "did this rewrite actually remove the misleading belief?" is only proven by the rerun, and `judged` predicates are LLM-graded.

---

