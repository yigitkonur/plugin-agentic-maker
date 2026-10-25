---
name: new
kind: plugin
target: ../..
runner: headless
isolation: clean
model: sonnet
max_turns: 45
timeout_s: 480
budget_usd: 2
allowed_tools: ["Read", "Glob", "Grep", "Write", "Edit", "Skill", "Bash(ls *)", "Bash(cat *)", "Bash(chmod *)", "Bash(grep *)", "Bash(mkdir *)", "Bash(python3 *)", "Bash(./inventory *)", "Bash(./seeded-cli list*)", "Bash(./seeded-cli get*)", "Bash(./seeded-cli --*)", "Bash(agentic-maker *)"]
---

## Prompt

/agentic-maker:build-cli a small command-line tool called inventory, as described in docs/inventory-spec.md. Save it as ./inventory in the current folder (one python3 file, executable).

## Implicit constraints

- It is built for an agent caller: parseable output, meaningful exit codes, never a prompt.
- The spec file stays as it is.
- It is probed with the plugin's own probe before it is called done.

## Fixtures

- copy: testdata/inventory-spec.md -> docs/inventory-spec.md

## Receipts

- exists: inventory
- cmd: test -x inventory => 0
- cmd: ./inventory --help </dev/null | grep -qi 'example' => 0
- cmd: ./inventory --help </dev/null | grep -qi 'exit' => 0
- cmd: ./inventory list --json </dev/null 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get("ok") is True else 1)' => 0
- cmd: ./inventory get nosuch --json </dev/null >/dev/null 2>&1; test $? -eq 3 => 0
- cmd: ./inventory frobnicate --json </dev/null >/dev/null 2>&1; test $? -eq 2 => 0
- cmd: ./inventory remove 1 </dev/null >/dev/null 2>&1; test $? -eq 2 => 0
- cmd: ./inventory remove 1 --dry-run --json </dev/null 2>/dev/null | python3 -c 'import sys,json; json.load(sys.stdin)' => 0
- cmd: ./inventory get nosuch --json </dev/null 2>/dev/null | python3 -c 'import sys,json; e=json.load(sys.stdin)["error"]; sys.exit(0 if e.get("code") and "retryable" in e and e.get("suggestion") else 1)' => 0
- cmd: agentic-maker --root "$(mktemp -d)" probe cli ./inventory --safe "list --json" --safe "get 1 --json" --safe "get nosuch --json # expect-exit 3" --safe "list --bogus --json # expect-exit 2" --sub remove --json 2>/dev/null | python3 -c "import sys,json; r=json.load(sys.stdin)['result']; sys.exit(1 if any(f.get('severity') in ('Critical','High') for f in r.get('findings', [])) else 0)" => 0
- unchanged: docs/inventory-spec.md
