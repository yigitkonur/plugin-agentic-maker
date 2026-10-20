#!/bin/sh
# Repo gate. Usage: scripts/check.sh [--strict-parity]
# Needs no network and no model. Runs on python 3.9 (/usr/bin/python3 on macOS) and whatever python3 is on PATH.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0
step() { printf '== %s\n' "$1"; }
bad()  { printf 'FAIL: %s\n' "$1"; fail=1; }
strict=0; [ "${1:-}" = "--strict-parity" ] && strict=1
PYS=""
for p in /usr/bin/python3 "$(command -v python3 2>/dev/null)"; do
  [ -n "$p" ] && [ -x "$p" ] && case " $PYS " in *" $p "*) ;; *) PYS="$PYS $p" ;; esac
done

step "shell syntax"
sh -n bin/agentic-maker && sh -n scripts/check.sh || bad "sh -n"

step "python compile"
for p in $PYS; do
  "$p" -c 'import sys; print("  ", sys.version.split()[0])'
  "$p" -I -c 'import sys,compileall; sys.exit(0 if compileall.compile_dir("lib",quiet=1,force=True) and compileall.compile_dir("scripts",quiet=1,force=True) else 1)' || bad "compile with $p"
done
find lib scripts -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null

step "CLI smoke (no model): doctor, normalize, check findings positive and negative control"
tmp=$(mktemp -d)
bin/agentic-maker doctor --json >"$tmp/doctor.json" 2>/dev/null; python3 -c 'import json,sys; sys.exit(0 if json.load(open(sys.argv[1]))["schema_version"]==1 else 1)' "$tmp/doctor.json" || bad "doctor envelope"
bin/agentic-maker normalize fixtures/traces/release-notes-untriggered/stream.jsonl --out "$tmp/n" --json >"$tmp/norm.json" 2>/dev/null || bad "normalize"
bin/agentic-maker check findings fixtures/traces/release-notes-untriggered/findings.json --trace "$tmp/n/trace.norm.jsonl" --root fixtures/skill-project --json >"$tmp/f.json" 2>/dev/null; rc=$?
[ "$rc" = 8 ] || bad "check findings should exit 8 (one verified, one fabricated rejected), got $rc"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); sys.exit(0 if d["result"]["verified_ids"]==["F1"] else 1)' "$tmp/f.json" || bad "only F1 may verify"
bin/agentic-maker run nope.md --json >/dev/null 2>&1; [ "$?" = 3 ] || bad "missing scenario must exit 3"
bin/agentic-maker run --json >/dev/null 2>&1; [ "$?" = 2 ] || bad "missing argument must exit 2"
printf 'not json' | bin/agentic-maker ledger gate >/dev/null 2>&1; [ "$?" = 0 ] || bad "gate must never fail a hook"
bin/agentic-maker normalize fixtures/traces/codex-rollout-sample.jsonl --out "$tmp/cx" --json >"$tmp/cx.json" 2>/dev/null; python3 -c 'import json,sys; d=json.load(open(sys.argv[1]))["result"]; sys.exit(0 if d["events"]>=6 and d["tool_calls"]==1 else 1)' "$tmp/cx.json" || bad "codex rollout adapter"
rm -f /tmp/seeded-cli-delete-ran
bin/agentic-maker probe cli fixtures/cli/seeded-cli/seeded-cli --safe-cmds fixtures/cli/seeded-cli/safe-cmds.txt --json >"$tmp/p1.json" 2>/dev/null; [ "$?" = 8 ] || bad "probe cli on the seeded CLI should exit 8"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1]))["result"]; sys.exit(0 if d["summary"]["findings"]>=10 else 1)' "$tmp/p1.json" || bad "probe cli should find at least 10 planted defects"
[ ! -e /tmp/seeded-cli-delete-ran ] || bad "SAFETY: probe cli executed the destructive command"
bin/agentic-maker probe cli fixtures/cli/clean-cli/clean-cli --safe-cmds fixtures/cli/clean-cli/safe-cmds.txt --json >/dev/null 2>&1; [ "$?" = 0 ] || bad "probe cli must report nothing on the clean twin"
bin/agentic-maker probe mcp "python3 fixtures/mcp/seeded-server.py" --call 'get_user={"id":"nope"}' --call 'export_all={}' --json >"$tmp/m1.json" 2>/dev/null; [ "$?" = 8 ] || bad "probe mcp on the seeded server should exit 8"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1]))["result"]; ids=" ".join(f["id"] for f in d["findings"]); need=["stdio.pollution","response.error_as_success.get_user","response.big.export_all","destructive.unmarked.delete_account","description.missing.ping_thing"]; sys.exit(0 if all(n in ids for n in need) and d["budget"]["tools"]==24 and d["budget"]["definition_chars"]==5724 else 1)' "$tmp/m1.json" || bad "probe mcp: planted defects or the hand-counted budget (24 tools, 5724 chars) not matched"
bin/agentic-maker probe mcp "python3 fixtures/mcp/clean-server.py" --call 'get_user={"id":"zz"}' --json >/dev/null 2>&1; [ "$?" = 0 ] || bad "probe mcp must report nothing on the clean server"
rm -rf "$tmp"

step "reference files: shape and size"
python3 scripts/lint-refs.py || bad "lint-refs"

step "skills: every injected !command must end in || true (a failing one aborts the whole skill silently)"
if [ -d skills ]; then
  hits=$(grep -rn -E '!`[^`]*`' skills --include=SKILL.md | grep -v '|| true' || true)
  [ -z "$hits" ] || { printf '%s\n' "$hits"; bad "injected command without || true"; }
fi

step "manifests"
python3 - <<'PY' || fail=1
import json, sys
p = json.load(open(".claude-plugin/plugin.json")); m = json.load(open(".claude-plugin/marketplace.json"))
v = m["plugins"][0]["version"]
ok = p["version"] == v == m["metadata"]["version"] and p["name"] == m["plugins"][0]["name"]
print("  plugin %s %s / marketplace %s" % (p["name"], p["version"], v))
bad = [k for k in p if k in ("commands", "agents", "skills", "hooks", "mcpServers")]
if bad: print("  manual path fields in plugin.json:", bad); ok = False
sys.exit(0 if ok else 1)
PY
[ "$?" = 0 ] || bad "manifest versions/names/path fields"
if command -v claude >/dev/null 2>&1; then
  out=$(claude plugin validate . 2>&1); echo "$out" | grep -q 'Validation passed' || { echo "$out"; bad "claude plugin validate"; }
else echo "  claude not found: skipped"; fi

step "safety: run --prepare never empties a directory it did not make; the Stop gate never hangs on a silent pipe"
sd=$(mktemp -d); mkdir "$sd/precious"; echo keep > "$sd/precious/important.txt"
python3 -I lib/agentic_maker/__main__.py --root fixtures/skill-project run release-notes --prepare --workspace-dir "$sd/precious" >/dev/null 2>&1; rc=$?
[ "$rc" = 5 ] && [ -f "$sd/precious/important.txt" ] || bad "--prepare touched a directory it did not make (exit $rc)"
python3 -I lib/agentic_maker/__main__.py --root fixtures/skill-project run release-notes --prepare --dry-run >/dev/null 2>&1; [ "$?" = 2 ] || bad "--prepare --dry-run must be a usage error"
rm -rf "$sd" fixtures/skill-project/.agentic-maker/runs fixtures/skill-project/.agentic-maker/active
python3 - <<'PY' || bad "ledger gate blocked on an open, silent stdin"
import subprocess, sys, time
p = subprocess.Popen([sys.executable, "-I", "lib/agentic_maker/__main__.py", "ledger", "gate"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
try:
    p.wait(timeout=8)
except subprocess.TimeoutExpired:
    p.kill(); sys.exit(1)
PY

step "eval-emit: a scenario becomes a claude plugin eval case (no model)"
ed=$(mktemp -d); trap 'rm -rf "$ed"' EXIT
python3 -I lib/agentic_maker/__main__.py --root fixtures/skill-project eval-emit release-notes --out "$ed" --json >/dev/null || bad "eval-emit failed"
[ -n "$(ls -A "$ed" 2>/dev/null)" ] || bad "eval-emit wrote nothing"

step "footprint: always-on cost of an installed copy (limit 400 tokens)"
if command -v claude >/dev/null 2>&1; then
  cfg=$(mktemp -d); here=$(pwd)
  det=$(cd "$cfg" && CLAUDE_CONFIG_DIR="$cfg" claude plugin marketplace add "$here" >/dev/null 2>&1 && CLAUDE_CONFIG_DIR="$cfg" claude plugin install agentic-maker@plugin-agentic-maker >/dev/null 2>&1 && CLAUDE_CONFIG_DIR="$cfg" claude plugin details agentic-maker 2>&1)
  rm -rf "$cfg"
  tok=$(printf '%s\n' "$det" | sed -n 's/.*Always-on:[^0-9]*\([0-9.]*\)\(k\)\{0,1\} *tok.*/\1\2/p' | head -1)
  echo "  always-on: ${tok:-unknown} tok"
  case "$tok" in ""|*k) bad "footprint unreadable or above 1k" ;; *) [ "${tok%.*}" -le 400 ] || bad "always-on footprint above 400 tokens" ;; esac
else echo "  claude not found: skipped"; fi

step "hygiene: no personal path, email or token anywhere in the tree"
# scan what git would publish (tracked + untracked, minus ignored); fall back to the whole tree outside git
if git rev-parse --git-dir >/dev/null 2>&1; then files=$(git ls-files -co --exclude-standard); else files=$(find . -path ./.git -prune -o -type f -print); fi
leaks=$(printf '%s\n' "$files" | grep -vE '(^|/)(check\.sh|lint-refs\.py|what-is-true\.md)$' | tr '\n' '\0' | xargs -0 grep -In -E '/Users/[A-Za-z]|@gmail\.|ghp_[A-Za-z0-9]{10,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{12,}|BEGIN (RSA |OPENSSH )?PRIVATE KEY' 2>/dev/null || true)
[ -z "$leaks" ] || { printf '%s\n' "$leaks" | head -20; bad "personal data pattern"; }
big=$(printf '%s\n' "$files" | while read -r f; do [ -f "$f" ] && [ "$(wc -c < "$f")" -gt 1000000 ] && echo "$f"; done)
[ -z "$big" ] || { echo "$big"; bad "file over 1 MB"; }
runs=$(find . -path ./.git -prune -o -type d -path '*/.agentic-maker/runs' -print)
[ -z "$runs" ] || { echo "$runs"; bad "run directories must not be committed or left in the tree"; }

step "parity (source headings -> destinations)"
if [ -d /tmp/am-src/skills-by-yigitkonur/skills ] || [ -n "${AM_SRC:-}" ]; then
  python3 scripts/parity.py check --no-write ${AM_SRC:+--src "$AM_SRC"}; prc=$?
  if [ "$prc" != 0 ]; then if [ "$strict" = 1 ]; then bad "parity"; else echo "  (informational until the migration is complete; use --strict-parity)"; fi; fi
else echo "  source clone not found: skipped (set AM_SRC)"; fi

[ "$fail" = 0 ] && echo "ALL CHECKS PASSED" || echo "CHECKS FAILED"
exit "$fail"
