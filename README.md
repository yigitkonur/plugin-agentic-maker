# agentic-maker

A Claude Code plugin for **making tools that agents use well** and **testing them against real agent behaviour**.

- **Design and audit** a CLI, script, MCP server or skill against one eight-question contract, using probes that run the thing the way an agent would instead of regex over source.
- **Derail** it: start a fresh agent on a realistic task, read the whole execution, find where it drifted, rewrite the text that caused the drift (not "do / don't" rules beside it), and rerun.

It works on any project and language: the probes act on the public interface (an executable, an MCP endpoint, a skill's text), and language code lives only in reference files that are read when needed.

```
/plugin marketplace add yigitkonur/plugin-agentic-maker
/plugin install agentic-maker@plugin-agentic-maker
```

Or from a shell in one step: `claude plugin install agentic-maker --marketplace yigitkonur/plugin-agentic-maker`.

Needs `python3` 3.9+ (standard library only) and, for fresh-agent runs, `claude` on PATH. Built and tested on Claude Code 2.1.302 (`claude plugin eval`, used by `eval-emit`, needs 2.1.269 or later). `herdr` is optional (live interactive rounds). Nothing else.

## Commands

| Command | What it does |
|---|---|
| `/agentic-maker:audit <target>` | Probes a CLI, script, MCP server or skill and reports against the contract with a scorecard and evidence. Changes nothing. |
| `/agentic-maker:derail <target>` | The loop: scenarios, fresh agents in a clean room, a read-only reader, verified findings, a fix of the controlling text, a rerun, and a Stop gate that refuses "fixed" without a fresh run. |
| `/agentic-maker:design <idea>` | Chooses CLI, MCP or skill, interviews you, and sketches the surface before any code. |
| `agent-interface-design` (model-invoked) | Write-time guidance when an agent-facing surface is being built or reviewed. |
| `derailment-method` (model-invoked, narrow) | The vocabulary and discipline of the method; preloaded into the reader. |

The CLI behind them is `agentic-maker` (on PATH while the plugin is enabled): `doctor`, `detect`, `scan`, `probe cli|cli-diff|mcp`, `run`, `normalize`, `check receipts|findings|diff|predicate|nice`, `ledger`, `eval-emit`. One JSON envelope on stdout when piped, diagnostics on stderr, exit codes 0-8, never a prompt. `agentic-maker <command> --help` has examples and the exit-code table.

## How a derailment run works

```
scenario (an everyday request that never names the target; receipts say what must be true afterwards)
  -> run: a fresh `claude -p` in a clean room (--restricted, only the target loaded), or a live herdr worker
  -> normalize: one trace with [n] references; nothing dropped silently
  -> check receipts: what the run left on disk (the agent's own report is only a claim)
  -> trace-reader (Read/Grep/Glob only): findings as JSON, each with a quote, the controlling text and a rerun predicate
  -> check findings: every quote must be verbatim in the cited events
  -> fix: rewrite the controlling text; check diff flags an edit that only adds a rule beside it
  -> rerun in a fresh session; check predicate decides
```

Why it is built this way, with the evidence: [docs/what-is-true.md](docs/what-is-true.md) (sixteen things checked against a real Claude Code), [docs/evidence/](docs/evidence/) (one file per capability, with the runs), [docs/design/](docs/design/README.md) (the plan this was built from).

## Status

Everything below was watched working on 2026-10-20 (Claude Code 2.1.302, herdr 0.9.5, macOS). "Fixture-tested" means exercised on planted-defect fixtures that live in this repo.

| Capability | Status | Evidence |
|---|---|---|
| Derail loop on a skill (headless, clean room) | watched working, full loop unattended | [04](docs/evidence/04-derail-loop.md) |
| Stop gate blocks a premature "fixed" | watched working in the real harness | [04](docs/evidence/04-derail-loop.md) |
| `audit` of a CLI (`probe cli`) | watched working; fixture-tested recall 10/11 (old script: 5/11), clean twin silent | [05](docs/evidence/05-audit-cli.md) |
| `audit` of an MCP server (`probe mcp`, stdio and HTTP) | watched working; budget equals a hand count | [06](docs/evidence/06-audit-mcp.md) |
| Live herdr round with a Claude worker | watched working, one round | [07](docs/evidence/07-live-herdr.md) |
| Ingest a Claude session transcript or `stream-json` | watched working | 04, 07 |
| Ingest a Codex rollout | parser built from real rollout files; no live Codex worker run | [07](docs/evidence/07-live-herdr.md) |
| agy | never launched (its command is an account-rotating wrapper); scrollback ingest only | [07](docs/evidence/07-live-herdr.md) |
| `eval-emit` (scenario -> `claude plugin eval` case) | watched working on one case | [08](docs/evidence/08-self-audit.md) |
| Authenticated MCP servers (OAuth) | not measured: reported as such, routed to `mcpc` / MCP Inspector | - |
| `design` skill | loads and routes; the interview is interactive and was not run end to end | [08](docs/evidence/08-self-audit.md) |
| Windows | not tested (macOS/Linux/WSL intended) | - |

## What it replaces

The three skills `audit-agentic-cli`, `audit-agentic-mcp` and `audit-skill-by-derailment` (from `yigitkonur/skills-by-yigitkonur`). Their reference content is carried into `skills/agent-interface-design/references/` as small single-decision files; every heading of the sources is accounted for in [docs/parity/ledger.tsv](docs/parity/ledger.tsv), and [docs/parity/REPORT.md](docs/parity/REPORT.md) lists what changed shape and what was dropped, with reasons.

## Footprint

Always-on cost is the descriptions of the model-invocable skills and the reader: about 309 tokens (`claude plugin details agentic-maker`). The three commands are user-started and add almost nothing until typed.

## Safety

- Probes run only `--help`, `--version`, one invalid command and commands you declare read-only; each in an empty temp directory with stdin closed, a timeout and its own process group. A script that does not read its arguments is not run at all. `agy` is never launched.
- Fresh-agent runs use `--restricted` and an allowlist of tools and environment variables; destructive-capable targets need throwaway fixtures. Every run has a turn cap, a budget ceiling and a time limit, and the cost preview comes before the spend.
- A live herdr round follows `herdr-conductor`'s rules: one command per reply, never poll, never touch the session's own pane. Accepting the trust dialog for a scratch folder adds an entry to `~/.claude.json` (use `run --prepare --workspace-dir` to reuse one folder).
- No telemetry, no network access except the one you point a probe at.

## Develop

`scripts/check.sh` (no network, no model): compiles on Python 3.9 and the current one, smoke-tests the CLI, lints the 300+ reference files (shape and size), checks links, injected-command safety, manifests and `claude plugin validate`, scans for personal data, and reports parity. See [AGENTS.md](AGENTS.md).

MIT licensed.
