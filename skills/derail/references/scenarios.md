# Scenarios

> Read when: you are writing, proposing or editing a scenario file, or its Receipts.

A scenario is a Markdown file in the **target project**: `.agentic-maker/scenarios/<name>.md`. Commit them; they are the regression suite for the target, written in prose.

```
---
name: add-json-output
kind: skill            # skill | plugin | cli | mcp
target: skills/my-skill          # a skill or plugin directory, a CLI binary path, or an MCP config / mcp-stdio:<command>
wrapper_name: notes              # skill dirs only: the namespace the worker sees (notes:my-skill)
bin: target/debug/mycli          # cli: the built executable (a crate or package name is not a path)
build: cargo build               # cli: how to produce it (the plugin does not run it unless asked)
env: ["FOO_API_BASE"]            # extra environment variable NAMES passed to the worker; no secrets by default
runner: headless                 # headless | existing
isolation: clean                 # clean (default) | in-situ
model: sonnet
max_turns: 25
timeout_s: 240
budget_usd: 0.8
allowed_tools: ["Read", "Glob", "Grep", "Skill", "Write", "Bash(python3 *)"]
permission_mode: dontAsk
---
## Prompt
## Implicit constraints
## Fixtures
## Receipts
```

Front matter is flat `key: value`, one key per line. A value that starts with `[`, `{`, `"`, a digit, `true`, `false` or `null` is parsed as JSON; anything else is a string. There is no YAML dependency.

## The four sections

- **Prompt:** exactly what a user would type. Everyday energy, two or three implicit constraints, **never the target's name or path** unless a user really would say it. Naming the target hides the most common skill failure - the skill not being chosen (T1) - and `run` warns when the prompt contains the target's name.
- **Implicit constraints:** what the worker is not told but a good result respects (the output goes in the working directory; inputs stay untouched). The reader checks these.
- **Fixtures:** how a fresh workspace is seeded. `- copy: src -> dest` lines (paths relative to the project) and, optionally, one fenced `sh` block run in the workspace with a minimal environment.
- **Receipts:** what must be true afterwards, one per line, evaluated by `agentic-maker check receipts`. This is the anti-self-report ledger.

## Receipt kinds

| Line | Passes when |
|---|---|
| `exists: path` / `absent: path` | the path exists / does not |
| `nonempty: path` | a file with at least one byte |
| `type: path json` (or `utf8`) | the file parses as that |
| `json: path key.0.sub == value` (`!=`, or `exists`) | the dotted path resolves to the value (value parsed as JSON) |
| `regex: path /pattern/flags` | the pattern is found in the file (`i m s x`) |
| `cmd: command => N` | the command, run in the workspace, exits N (default 0) |
| `mtime-in-window: path` | the file was written during the run |
| `unchanged: path` | identical to the seeded file |
| `no-extra-files: dir allow=glob,glob` | nothing new except what matches the globs |

Paths are relative to the workspace and cannot leave it. Pick the receipts from the task, not from a template: they exist to catch "done" claims that the disk contradicts (see `derailment-method/references/evidence-and-anti-sycophancy.md`).

## A good set of three (propose these when none exist)

1. **A normal task** in the words a user would use. The baseline: does the target get chosen, read and followed?
2. **An ambiguous task** where the target's text has to resolve a choice (which format, which file). Finds M1, M2, M5.
3. **A failure-injection task**: a missing prerequisite, a stale flag, an input that breaks a parser. Finds O1, O3, O5 and whether errors teach.

Add a **scale** scenario (many files, a long input) when the target claims to handle volume (O4). Run several takes of each: agents are not deterministic, and one clean take proves little.

## Approvals (live runs only)

`approvals: [{"match": "Do you trust", "keys": "enter"}]` lists the dialogs a live herdr run may answer. Any other dialog is a finding (real user friction) and ends the run as `needs_decision`. The headless runner has no dialogs: tools outside `allowed_tools` are denied and the denials are reported.
