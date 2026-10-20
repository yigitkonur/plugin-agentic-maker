> Part of the `agentic-maker` plan · [README](README.md)

## 8. On disk

```
agentic-maker/
├── .claude-plugin/plugin.json            # name, version, description, keywords — NO path fields (swiftui gotcha)
├── README.md                             # 3 flows, install, degrade matrix, footprint numbers
├── bin/agentic-maker                         # shim → lib/ ; Python 3.9+ stdlib only; `--json` envelope with next_actions; exit 0/2/3/4/5
├── lib/                                  # v1 (M1): doctor, run, normalize/{claude,text}, check{receipts,findings,diff,nice}, ledger
│                                         # later: probe_cli (M2), normalize/{codex,agy} (M3), probe_mcp + scan + detect (M4), eval_emit (M5)
├── surfaces.tsv                          # (M2+) kind | detect signals | probe | rubric | exposure  (new target kind = 1 row + 2 md files)
├── skills/
│   ├── derail/            SKILL.md (DMI; hooks: H2) + references/{loop,scenarios,clean-room,synthesis-matrix}.md
│   │                      references/runners/{headless,eval,herdr,existing}.md · harnesses/{claude,codex,agy}.md · targets/{skill,plugin,cli,mcp}.md
│   ├── audit/             SKILL.md (DMI, context: fork, background: false) + references/{report,scoring}.md
│   ├── design/            SKILL.md (DMI) + references/{interview,sketch-template}.md
│   (no `setup` skill in v1: `agentic-maker doctor` + README carry setup; `.agentic-maker/config.md` only if a real need appears)
│   ├── agent-interface-design/            # model-invocable
│   │   ├── SKILL.md                       # contract + routing table (read-when) + pitfalls
│   │   └── references/{contract.md, decisions/, cli/, mcp/, skill/, frameworks/, fresh/}
│   └── derailment-method/                 # user-invocable:false
│       ├── SKILL.md                       # invariants, markers, severity, fix discipline
│       └── references/{taxonomy, fix-patterns, reading-traces, evidence-and-anti-sycophancy, finding-schema}.md
├── agents/trace-reader.md
├── scripts/                              # check.sh, parity.py (H2 lives in skills/derail frontmatter — M0 U4)
├── evals/                                # claude plugin eval: trigger/negative cases + seeded-defect audit cases
├── fixtures/                             # seeded-defect CLI (bash), MCP (python stdlib), skill — parity + regression
└── workflows/derail-matrix.js            # M5+, optional
```
Rules: every reference ≤ ~8 KB, one decision, stable headings; **language code lives only in `frameworks/`**, loaded for the detected stack; no sidecar `.sh.md` docs — `agentic-maker <cmd> --help` (examples + exit codes) is the doc, as our own audit demands.

---


---
### Claims to verify
- U4 (hook placement), U12 (footprint). `claude plugin validate --strict` must pass on the layout; no manual path fields in `plugin.json`.
