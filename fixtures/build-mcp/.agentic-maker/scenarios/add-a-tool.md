---
name: add-a-tool
kind: plugin
target: ../..
leave_out: ["fixtures", "evals", "docs"]
runner: headless
isolation: clean
model: sonnet
max_turns: 45
timeout_s: 480
budget_usd: 2
allowed_tools: ["Read", "Glob", "Grep", "Write", "Edit", "Skill", "Bash(ls *)", "Bash(cat *)", "Bash(grep *)", "Bash(mkdir *)", "Bash(python3 *)", "Bash(printf *)", "Bash(agentic-maker *)"]
---

## Prompt

/agentic-maker:build-mcp our MCP server in server/server.py has get_user, list_users and delete_user. Add one more tool that suspends a user account by id. Suspending can be undone, so it is not a deletion. Keep it consistent with the other tools.

## Implicit constraints

- The new tool is `suspend_user`, takes the user id, and is marked as a safe-to-retry, non-destructive write.
- It follows the conventions of the existing tools (descriptions that say when to use it, errors that teach, a flat schema).
- The three existing tools keep working, and `delete_user` keeps its destructive marking.
- It is probed with the plugin's own probe before it is called done.

## Fixtures

- copy: testdata/_mini.py -> server/_mini.py
- copy: testdata/clean-server.py -> server/server.py

## Receipts

- cmd: printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}' '{"jsonrpc":"2.0","method":"notifications/initialized"}' '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | python3 server/server.py 2>/dev/null | grep -q '"suspend_user"' => 0
- cmd: printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}' '{"jsonrpc":"2.0","method":"notifications/initialized"}' '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | python3 server/server.py 2>/dev/null | python3 -c "import sys,json; ts=[json.loads(l) for l in sys.stdin if l.strip()][-1]['result']['tools']; t=[x for x in ts if x['name']=='suspend_user'][0]; s=t['inputSchema']; ok='id' in s['required'] and len(s['properties'])<=6 and t.get('annotations',{}).get('destructiveHint') is False and 20<len(t['description'])<400; sys.exit(0 if ok else 1)" => 0
- cmd: printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}' '{"jsonrpc":"2.0","method":"notifications/initialized"}' '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | python3 server/server.py 2>/dev/null | python3 -c "import sys,json; ts={x['name']:x for x in [json.loads(l) for l in sys.stdin if l.strip()][-1]['result']['tools']}; ok=all(n in ts for n in ('get_user','list_users','delete_user')) and ts['delete_user']['annotations']['destructiveHint'] is True; sys.exit(0 if ok else 1)" => 0
- cmd: agentic-maker --root "$(mktemp -d)" probe mcp "python3 server/server.py" --call 'get_user={"id":"1"}' --json 2>/dev/null | python3 -c "import sys,json; r=json.load(sys.stdin)['result']; sys.exit(1 if any(f.get('severity') in ('Critical','High') for f in r.get('findings', [])) else 0)" => 0
- unchanged: server/_mini.py
