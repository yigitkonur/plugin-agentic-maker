---
name: repair
kind: plugin
target: ../..
runner: headless
isolation: clean
model: sonnet
max_turns: 60
timeout_s: 480
budget_usd: 2
allowed_tools: ["Read", "Glob", "Grep", "Write", "Edit", "Skill", "Bash(ls *)", "Bash(cat *)", "Bash(grep *)", "Bash(mkdir *)", "Bash(python3 *)", "Bash(printf *)", "Bash(agentic-maker *)"]
---

## Prompt

/agentic-maker:build-mcp the MCP server in server/server.py is hard for AI agents to use: they pick the wrong tool, get confusing answers and are one call away from deleting things. Fix it so an agent can use it well. Do not call its delete or export tools.

## Implicit constraints

- The server keeps serving over stdio; `_mini.py` is the protocol loop and stays as it is.
- Tools that are duplicates, unnamed or undocumented are fixed or merged, not left; a destructive tool is marked as destructive.
- It is probed with the plugin's own probe before it is called done.

## Fixtures

- copy: testdata/_mini.py -> server/_mini.py
- copy: testdata/seeded-server.py -> server/server.py

## Receipts

- cmd: agentic-maker --root "$(mktemp -d)" probe mcp "python3 server/server.py" --call 'get_user={"id":"nope"}' --json 2>/dev/null | python3 -c "import sys,json; r=json.load(sys.stdin)['result']; sys.exit(1 if any(f.get('severity') in ('Critical','High') for f in r.get('findings', [])) else 0)" => 0
- cmd: python3 server/server.py </dev/null 2>/dev/null | head -c 1 | grep -q '{' ; test $? -ne 0 => 0
- cmd: printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}' '{"jsonrpc":"2.0","method":"notifications/initialized"}' '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | python3 server/server.py 2>/dev/null | python3 -c "import sys,json; ts=[json.loads(l) for l in sys.stdin if l.strip()][-1]['result']['tools']; d=[t for t in ts if 'delete' in t['name'].lower()]; sys.exit(0 if d and all(t.get('annotations',{}).get('destructiveHint') is True for t in d) else 1)" => 0
- cmd: printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}' '{"jsonrpc":"2.0","method":"notifications/initialized"}' '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | python3 server/server.py 2>/dev/null | python3 -c "import sys,json,re; ts=[json.loads(l) for l in sys.stdin if l.strip()][-1]['result']['tools']; ok=all(t.get('description') and re.match(r'^[A-Za-z0-9_-]+$', t['name']) and len(t['description'])<=400 for t in ts); sys.exit(0 if ok else 1)" => 0
- unchanged: server/_mini.py
