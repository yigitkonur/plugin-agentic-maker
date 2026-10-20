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

step "hygiene: no personal path, email or token anywhere in the tree"
leaks=$(grep -rIn -E '/Users/[A-Za-z]|@gmail\.|ghp_[A-Za-z0-9]{10,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{12,}|BEGIN (RSA |OPENSSH )?PRIVATE KEY' . \
  --exclude-dir=.git --exclude-dir=node_modules --exclude=check.sh --exclude=lint-refs.py --exclude=what-is-true.md || true)
[ -z "$leaks" ] || { printf '%s\n' "$leaks" | head -20; bad "personal data pattern"; }
big=$(find . -path ./.git -prune -o -type f -size +1000k -print)
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
