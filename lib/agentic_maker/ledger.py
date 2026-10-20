"""The derail run ledger: the file that survives compaction, and the brain of the Stop gate.

One ledger per orchestrator session, at <root>/.agentic-maker/runs/<run_id>/ledger.json, found through a
pointer <root>/.agentic-maker/active/<session_id>.json. The gate (a Stop hook) blocks only one situation:
the target was edited after the newest completed trace while a fix is in flight, i.e. "fixed" is about to be
claimed with no fresh evidence. Every other situation passes silently.
"""
import json
import os
import re
import shutil
import sys
import time

from agentic_maker.common import ensure_state_gitignore, newest_mtime, now_iso, read_json, runs_dir, state_dir, write_json
from agentic_maker.envelope import CliError

PASS_STATUSES = {"awaiting_user", "closed", "unverified-recorded", "abandoned"}
SETTABLE = {"framing", "running", "reading", "fixing", "awaiting_user"}


def _pointer(root, session):
    return os.path.join(state_dir(root), "active", "%s.json" % session)


def _path(root, run_id):
    return os.path.join(runs_dir(root), run_id, "ledger.json")


def load(root, session=None, run_id=None):
    if run_id:
        return read_json(_path(root, run_id)), _path(root, run_id)
    if session:
        ptr = _pointer(root, session)
        if not os.path.exists(ptr):
            raise CliError("not_found", "no_active_ledger", "no active ledger for session %s under %s" % (session, root),
                           suggestion="agentic-maker ledger init --session <id> --target <path>")
        p = read_json(ptr)
        return read_json(p["ledger"]), p["ledger"]
    raise CliError("usage", "session_or_run", "pass --session <id> or --run-id <id>")


def init(root, session, targets, run_id=None, budget_usd=10.0, rounds=5, ttl_hours=6.0, force=False):
    if not session:
        raise CliError("usage", "session_required", "ledger init needs --session (use ${CLAUDE_SESSION_ID} inside a skill)")
    if not re.match(r"^[A-Za-z0-9_-]+$", session):
        raise CliError("usage", "bad_session_id", "session id %r: only letters, digits, - and _ are allowed" % session, suggestion="use ${CLAUDE_SESSION_ID}")
    if run_id and not re.match(r"^[A-Za-z0-9_.-]+$", run_id):
        raise CliError("usage", "bad_run_id", "run id %r: only letters, digits, . - and _ are allowed" % run_id)
    ptr = _pointer(root, session)
    if os.path.exists(ptr) and not force:
        cur = read_json(read_json(ptr)["ledger"])
        if cur["status"] not in PASS_STATUSES:
            raise CliError("conflict", "ledger_active", "session %s already has an open ledger (%s, status %s)" % (session, cur["run_id"], cur["status"]),
                           suggestion="agentic-maker ledger close|abandon first, or pass --force")
    run_id = run_id or "%s-derail" % time.strftime("%Y%m%d-%H%M%S")
    if os.path.exists(_path(root, run_id)):
        raise CliError("conflict", "run_id_exists", "a ledger for run %s already exists" % run_id, suggestion="pick another --run-id, or omit it for a fresh one")
    tpaths = [t if os.path.isabs(t) else os.path.abspath(os.path.join(root, t)) for t in targets]
    for t in tpaths:
        if not os.path.exists(t):
            raise CliError("not_found", "target_not_found", "target does not exist: %s" % t)
    led = {
        "run_id": run_id, "session_id": session, "root": root, "status": "framing", "created_at": now_iso(),
        "created_epoch": time.time(), "ttl_hours": ttl_hours, "targets": tpaths, "rounds_max": rounds,
        "budget_usd_total": budget_usd, "spent_usd": 0.0, "traces": [], "last_trace_epoch": 0.0,
        "findings": {}, "unverified": [], "events": [{"t": now_iso(), "event": "init"}],
    }
    ensure_state_gitignore(root)
    p = _path(root, run_id)
    write_json(p, led)
    write_json(ptr, {"run_id": run_id, "ledger": p})
    return led


def save(led, path):
    write_json(path, led)


def event(led, name, **kw):
    led["events"].append(dict({"t": now_iso(), "event": name}, **kw))


def record_trace(root, session, take_dir):
    led, p = load(root, session=session)
    run = read_json(os.path.join(take_dir, "run.json"))
    stats = run.get("stats") or {}
    end = run.get("finished_at_epoch") or os.path.getmtime(os.path.join(take_dir, "run.json"))
    led["traces"].append({"take_dir": take_dir, "scenario": run.get("scenario"), "status": run.get("status"),
                          "finished_epoch": end, "cost_usd": stats.get("cost_usd", 0)})
    led["last_trace_epoch"] = max(led.get("last_trace_epoch", 0.0), end)
    led["spent_usd"] = round(led.get("spent_usd", 0.0) + float(stats.get("cost_usd", 0) or 0), 6)
    event(led, "trace", take_dir=take_dir, status=run.get("status"))
    if led["status"] == "fixing":
        led["status"] = "running"
    save(led, p)
    return led


def _covered(path, targets):
    return any(path == t or path.startswith(t.rstrip(os.sep) + os.sep) for t in targets)


def refuse_if_over_budget(root, session):
    """`run --session` calls this before it spends: the ceiling covers the workers' recorded cost (readers are not metered)."""
    try:
        led, _ = load(root, session=session)
    except CliError:
        return          # no ledger: nothing to enforce (the caller warns)
    if led.get("spent_usd", 0) >= led.get("budget_usd_total", 1e9):
        raise CliError("conflict", "budget_exhausted", "the ledger's budget is spent: $%s of $%s" % (led["spent_usd"], led["budget_usd_total"]),
                       suggestion="agentic-maker ledger close --session %s --outcome open --reason \"budget spent\"; or start a new ledger with a larger --budget-usd" % session)


def _snapshot(root, led, fid, findings, fp):
    """Keep the controlling file as it was when this fix started: `check diff` judges the edit against it, not against git HEAD."""
    rel = os.path.relpath(fp, root)
    rel = rel if not rel.startswith("..") else os.path.join("_outside", fp.lstrip(os.sep))
    dest = os.path.join(runs_dir(root), led["run_id"], "snapshots", fid, rel)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copy2(fp, dest)
    led.setdefault("snapshots", {}).setdefault(fid, []).append({"file": fp, "snapshot": dest})


def fix(root, session, finding_ids, verified_ids, trace_norm=None, findings_path=None):
    led, p = load(root, session=session)
    bad = [f for f in finding_ids if f not in verified_ids]
    if bad:
        raise CliError("validation", "finding_not_verified", "refusing to fix unverified finding(s): %s" % ", ".join(bad),
                       suggestion="agentic-maker check findings <file> --trace <trace.norm.jsonl>; the reader's claims are leads until the quotes check out")
    if led.get("rounds_used", 0) >= led.get("rounds_max", 5):
        raise CliError("conflict", "rounds_exhausted", "round limit reached: %d of %d fix rounds used" % (led.get("rounds_used", 0), led.get("rounds_max", 5)),
                       suggestion="agentic-maker ledger close --session %s --outcome open --reason \"round limit\"; the remaining findings are reported as open" % session)
    led["rounds_used"] = led.get("rounds_used", 0) + 1
    for fid in finding_ids:
        led["findings"][fid] = {"status": "fixing", "since": now_iso()}
    led["status"] = "fixing"
    if findings_path:
        # the gate must watch every file a fix will touch, even one the opening --target list missed
        data = read_json(findings_path)
        for f in (data.get("findings") if isinstance(data, dict) else data) or []:
            ct = (f or {}).get("controlling_text") or {}
            if f.get("id") in finding_ids and ct.get("file"):
                fp = ct["file"] if os.path.isabs(ct["file"]) else os.path.abspath(os.path.join(root, ct["file"]))
                if not _covered(fp, led["targets"]):
                    led["targets"].append(fp)
                if os.path.isfile(fp):
                    _snapshot(root, led, f["id"], data, fp)
    if trace_norm and os.path.exists(trace_norm):
        # the trace these findings came from is the evidence the fix must be re-tested against
        led["fix_base_epoch"] = max(led.get("fix_base_epoch", 0.0), os.path.getmtime(trace_norm))
    event(led, "fix", findings=finding_ids)
    save(led, p)
    return led


def set_status(root, session, status, reason=None):
    if status not in SETTABLE:
        raise CliError("usage", "bad_status", "status must be one of %s" % "|".join(sorted(SETTABLE)))
    led, p = load(root, session=session)
    led["status"] = status
    event(led, "status", status=status, reason=reason)
    save(led, p)
    return led


def finish(root, session, kind, reason, outcome=None):
    led, p = load(root, session=session)
    if kind == "abandon":
        led["status"] = "abandoned"
    elif outcome == "unverified":
        led["status"] = "unverified-recorded"
        led["unverified"].append(reason)
    else:
        led["status"] = "closed"
    led["outcome"] = outcome or kind
    led["reason"] = reason
    event(led, kind, outcome=outcome, reason=reason)
    save(led, p)
    return led


def _find_pointer(session, cwd_candidates):
    for c in cwd_candidates:
        if not c:
            continue
        d = os.path.abspath(c)
        for _ in range(8):
            ptr = _pointer(d, session)
            if os.path.exists(ptr):
                return d, ptr
            parent = os.path.dirname(d)
            if parent == d:
                break
            d = parent
    return None, None


def gate(stdin_text, env=None):
    """Return (exit_code, stdout_text). Never raises: a hook that crashes must not trap the agent."""
    env = env if env is not None else os.environ
    try:
        if env.get("AGENTIC_MAKER_HOOKS", "").lower() == "off":
            return 0, ""
        if not stdin_text.strip():
            return 0, ""
        payload = json.loads(stdin_text)
        session = payload.get("session_id")
        if not session:
            return 0, ""
        root, ptr = _find_pointer(session, [payload.get("cwd"), env.get("CLAUDE_PROJECT_DIR")])
        if not ptr:
            return 0, ""
        led = read_json(read_json(ptr)["ledger"])
        if payload.get("stop_hook_active") or payload.get("background_tasks"):
            return 0, ""
        if led["status"] in PASS_STATUSES:
            return 0, ""
        if time.time() - led.get("created_epoch", 0) > float(led.get("ttl_hours", 6)) * 3600:
            return 0, ""
        if led.get("spent_usd", 0) >= led.get("budget_usd_total", 1e9):
            return 0, ""
        if led["status"] != "fixing":
            return 0, ""
        last = max(led.get("last_trace_epoch", 0.0), led.get("fix_base_epoch", 0.0))
        newest = newest_mtime(led["targets"])
        if newest <= last + 1.0:
            return 0, ""
        changed = []
        for t in led["targets"]:
            for dp, dns, fns in (os.walk(t) if os.path.isdir(t) else [(os.path.dirname(t), [], [os.path.basename(t)])]):
                dns[:] = [d for d in dns if d not in (".git", "__pycache__", ".agentic-maker")]
                for fn in fns:
                    fp = os.path.join(dp, fn)
                    try:
                        if os.path.getmtime(fp) > last + 1.0:
                            changed.append(os.path.relpath(fp, root))
                    except OSError:
                        pass
        close_cmd = 'agentic-maker ledger close --session %s --outcome unverified --reason "<why>"' % session
        abandon_cmd = 'agentic-maker ledger abandon --session %s --reason "<why>"' % session
        if last <= 0:
            what = "no run has completed for this ledger yet, so nothing has tested the change to %s" % ", ".join(sorted(changed)[:4])
        else:
            what = "%d target file(s) changed after the newest completed trace (%s%s)" % (
                len(changed), ", ".join(sorted(changed)[:4]), ", ..." if len(changed) > 4 else "")
        reason = (
            "A derail fix is in flight and %s. Do not report this as fixed: no fresh run has seen the change. Pick one: "
            "(1) rerun the scenario in a fresh session: agentic-maker run <scenario> --session %s; "
            "(2) record that it could not be verified: %s; "
            "(3) stop the loop: %s." % (what, session, close_cmd, abandon_cmd))
        return 0, json.dumps({"decision": "block", "reason": reason})
    except Exception as e:  # never trap the agent
        sys.stderr.write("agentic-maker gate: ignored internal error: %s\n" % e)
        return 0, ""
