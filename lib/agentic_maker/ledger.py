"""The derail run ledger: the file that survives compaction, and the brain of the Stop gate.

One ledger per orchestrator session, at <root>/.agentic-maker/runs/<run_id>/ledger.json, found through a
pointer <root>/.agentic-maker/active/<session_id>.json. The gate (a Stop hook) blocks only one situation:
the target was edited after the newest completed trace while a fix is in flight, i.e. "fixed" is about to be
claimed with no fresh evidence. Every other situation passes silently.
"""
import hashlib
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


def record_trace(root, session, take_dir, receipts=None):
    """One entry per take: recording a take again replaces its entry (and its cost) instead of adding a second one."""
    led, p = load(root, session=session)
    run = read_json(os.path.join(take_dir, "run.json"))
    stats = run.get("stats") or {}
    end = run.get("finished_at_epoch") or os.path.getmtime(os.path.join(take_dir, "run.json"))
    if receipts is None and os.path.isfile(os.path.join(take_dir, "receipts.json")):
        rc = read_json(os.path.join(take_dir, "receipts.json"))
        receipts = {"total": rc.get("total"), "passed": rc.get("passed"), "failed": rc.get("failed"),
                    "failures": [{"kind": r["kind"], "spec": r["spec"], "detail": r["detail"]} for r in rc.get("receipts", []) if not r.get("ok")]}
    entry = {"take_dir": take_dir, "scenario": run.get("scenario"), "status": run.get("status"),
             "finished_epoch": end, "cost_usd": stats.get("cost_usd", 0), "receipts": receipts}
    same = [i for i, t in enumerate(led["traces"]) if os.path.realpath(t["take_dir"]) == os.path.realpath(take_dir)]
    for i in same:
        led["spent_usd"] = round(led.get("spent_usd", 0.0) - float(led["traces"][i].get("cost_usd", 0) or 0), 6)
    led["traces"] = [t for i, t in enumerate(led["traces"]) if i not in same] + [entry]
    led["last_trace_epoch"] = max(t.get("finished_epoch", 0.0) for t in led["traces"])
    led["target_digest"] = _digest(led["targets"])
    led["spent_usd"] = round(led.get("spent_usd", 0.0) + float(stats.get("cost_usd", 0) or 0), 6)
    event(led, "trace", take_dir=take_dir, status=run.get("status"))
    if led["status"] == "fixing":
        led["status"] = "running"
    save(led, p)
    return led


def _digest(targets, limit=3000):
    """sha1 of every file under the targets (what the files said when a take was recorded): content, not mtime, decides whether a file was edited since."""
    out = {}
    for t in targets:
        walk = os.walk(t) if os.path.isdir(t) else [(os.path.dirname(t), [], [os.path.basename(t)])]
        for dp, dns, fns in walk:
            dns[:] = [d for d in dns if d not in (".git", "__pycache__", ".agentic-maker", "node_modules")]
            for fn in fns:
                fp = os.path.join(dp, fn)
                if len(out) >= limit:
                    return out
                try:
                    if os.path.getsize(fp) < 5 * 1024 * 1024:
                        with open(fp, "rb") as f:
                            out[fp] = hashlib.sha1(f.read()).hexdigest()
                except OSError:
                    pass
    return out


def _file_digest(fp):
    try:
        with open(fp, "rb") as f:
            return hashlib.sha1(f.read()).hexdigest()
    except OSError:
        return None


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


def fkey(root, findings_path, fid):
    """Every reader numbers its findings F1, F2...: a finding is identified by the file it came from and its id."""
    fp = findings_path if os.path.isabs(findings_path) else os.path.join(root, findings_path)
    return "%s#%s" % (os.path.relpath(os.path.abspath(fp), root), fid)


def _snapshot(root, led, key, fp):
    """Keep the controlling file as it was when this fix started: `check diff` judges the edit against it, not against git HEAD."""
    rel = os.path.relpath(fp, root)
    rel = rel if not rel.startswith("..") else os.path.join("_outside", fp.lstrip(os.sep))
    dest = os.path.join(runs_dir(root), led["run_id"], "snapshots", re.sub(r"[^A-Za-z0-9_.-]", "_", key), rel)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copy2(fp, dest)
    led.setdefault("snapshots", {}).setdefault(key, []).append({"file": fp, "snapshot": dest})


def _findings_items(findings_path):
    data = read_json(findings_path)
    return [f for f in ((data.get("findings") if isinstance(data, dict) else data) or []) if isinstance(f, dict)]


def fix(root, session, finding_ids, verified_ids, trace_norm=None, findings_path=None):
    led, p = load(root, session=session)
    bad = [f for f in finding_ids if f not in verified_ids]
    if bad:
        raise CliError("validation", "finding_not_verified", "refusing to fix unverified finding(s): %s" % ", ".join(bad),
                       suggestion="agentic-maker check findings <file> --trace <trace.norm.jsonl>; the reader's claims are leads until the quotes check out")
    if led.get("status") != "fixing" and led.get("rounds_used", 0) >= led.get("rounds_max", 5):
        raise CliError("conflict", "rounds_exhausted", "round limit reached: %d of %d fix rounds used" % (led.get("rounds_used", 0), led.get("rounds_max", 5)),
                       suggestion="agentic-maker ledger close --session %s --outcome open --reason \"round limit\"; the remaining findings are reported as open" % session)
    by_id = {f.get("id"): f for f in _findings_items(findings_path)} if findings_path else {}
    # the copy `check diff` compares with must be the file BEFORE the fix; if its content changed since the newest recorded run, the fix cannot be judged
    first_of_round = led.get("status") != "fixing"
    digest = led.get("target_digest") or {}
    if first_of_round and digest:
        for fid in finding_ids:
            ct = (by_id.get(fid) or {}).get("controlling_text") or {}
            if ct.get("file"):
                fp = ct["file"] if os.path.isabs(ct["file"]) else os.path.abspath(os.path.join(root, ct["file"]))
                if fp in digest and os.path.isfile(fp) and _file_digest(fp) != digest[fp]:
                    raise CliError("conflict", "edited_before_fix",
                                   "%s changed after the newest recorded run and before `ledger fix` kept a copy of it: the fix to %s could not be judged against what it replaced" % (ct["file"], fid),
                                   suggestion="restore the file (git checkout -- %s, or undo the edit), run `ledger fix` again, then make the edit" % ct["file"])
    if first_of_round:                      # a round is a batch of fixes followed by a rerun: a second `ledger fix` before the rerun joins it
        led["rounds_used"] = led.get("rounds_used", 0) + 1
    fix_epoch = time.time()
    for fid in finding_ids:
        key = fkey(root, findings_path, fid) if findings_path else fid
        led["findings"][key] = {"status": "fixing", "since": now_iso(), "fix_epoch": fix_epoch, "id": fid,
                                "findings_file": os.path.relpath(os.path.abspath(findings_path if os.path.isabs(findings_path) else os.path.join(root, findings_path)), root) if findings_path else None}
    led["status"] = "fixing"
    if findings_path:
        # the gate must watch every file a fix will touch, even one the opening --target list missed
        for fid in finding_ids:
            ct = (by_id.get(fid) or {}).get("controlling_text") or {}
            if ct.get("file"):
                fp = ct["file"] if os.path.isabs(ct["file"]) else os.path.abspath(os.path.join(root, ct["file"]))
                if not _covered(fp, led["targets"]):
                    led["targets"].append(fp)
                if os.path.isfile(fp):
                    _snapshot(root, led, fkey(root, findings_path, fid), fp)
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
    if kind == "close" and outcome == "clean":
        problems, nxt = witness_problems(led, session)
        if problems:
            raise CliError("conflict", "not_witnessed", "the loop cannot be closed as clean: %s" % "; ".join(problems), details={"missing": problems},
                           next_actions=nxt, suggestion="do the next action, or close with --outcome unverified|open and say why")
    if kind == "abandon":
        led["status"] = "abandoned"
    elif outcome == "unverified":
        led["status"] = "unverified-recorded"
        led["unverified"].append(reason)
    else:
        led["status"] = "closed"
    led["outcome"] = outcome or kind
    led["reason"] = reason
    resolved = {"abandon": "abandoned", "unverified": "unverified", "open": "open", "clean": "fixed"}.get(outcome if kind != "abandon" else kind, "open")
    for f in led["findings"].values():
        if f.get("status") == "fixing":
            f["status"] = resolved
    event(led, kind, outcome=outcome, reason=reason)
    save(led, p)
    return led


def _newest_trace(led):
    return max(led["traces"], key=lambda t: t.get("finished_epoch", 0)) if led.get("traces") else None


def _verdict_is_fresh(f):
    pr = f.get("predicate") or {}
    return pr.get("passed") is True and pr.get("take_epoch", 0) > f.get("fix_epoch", 0)


def witness_problems(led, session):
    """What stands between this ledger and an honest `clean`: a fix is witnessed by a predicate that passed on a take run after it, and the receipts of the newest take."""
    problems, nxt = [], []
    newest = _newest_trace(led)
    scen = (newest or {}).get("scenario") or "<scenario>"
    if not newest:
        return ["no run has completed in this ledger"], [{"command": "agentic-maker run %s --session %s" % (scen, session), "why": "a clean loop starts from a run"}]
    rc = newest.get("receipts")
    if rc is None:
        problems.append("the receipts of the newest take were never evaluated")
        nxt.append({"command": "agentic-maker check receipts %s --session %s" % (newest["take_dir"], session), "why": "record what the run left on disk"})
    elif rc.get("total") and rc.get("failed"):
        problems.append("%d of %d receipts fail in the newest take" % (rc["failed"], rc["total"]))
        nxt.append({"command": "agentic-maker run %s --session %s" % (scen, session), "why": "rerun after the fix; the receipts decide"})
    fixing = [(k, f) for k, f in led.get("findings", {}).items() if f.get("status") == "fixing"]
    for k, f in fixing:
        pr = f.get("predicate")
        if not pr:
            problems.append("%s: no rerun-predicate verdict is recorded" % k)
            if newest.get("finished_epoch", 0) > f.get("fix_epoch", 0):
                nxt.append({"command": "agentic-maker check predicate --findings %s --trace %s --session %s" % (f.get("findings_file"), os.path.join(newest["take_dir"], "trace.norm.jsonl"), session),
                            "why": "judge the fix against the rerun"})
            else:
                nxt.append({"command": "agentic-maker run %s --session %s" % (scen, session), "why": "no run has finished since the fix"})
        elif pr.get("passed") is not True:
            problems.append("%s: its rerun predicate was not met" % k)
        elif not _verdict_is_fresh(f):
            problems.append("%s: its verdict comes from a take that finished before the fix" % k)
            nxt.append({"command": "agentic-maker run %s --session %s" % (scen, session), "why": "run again after the fix"})
    seen, uniq = set(), []
    for n in nxt:
        if n["command"] not in seen:
            seen.add(n["command"])
            uniq.append(n)
    return problems, uniq


def phase_and_next(led, session):
    """Where the loop is, computed from state, and the one command that moves it: what a compacted or confused orchestrator needs."""
    newest = _newest_trace(led)
    if not newest:
        return "framing", [{"command": "agentic-maker run <scenario> --session %s" % session, "why": "no take yet: preview with --dry-run, then run"}]
    scen = newest.get("scenario") or "<scenario>"
    fixing = [f for f in led.get("findings", {}).values() if f.get("status") == "fixing"]
    reads = [r for r in led.get("reads", []) if r.get("take_dir") == newest["take_dir"]]
    if fixing:
        if newest.get("finished_epoch", 0) <= max(f.get("fix_epoch", 0) for f in fixing):
            return "rerunning", [{"command": "agentic-maker run %s --session %s" % (scen, session), "why": "the fix has not been run yet; the edit and the check diff come first"}]
        if not all(_verdict_is_fresh(f) or (f.get("predicate") or {}).get("passed") is False for f in fixing):
            files = sorted({f.get("findings_file") for f in fixing if f.get("findings_file")})
            return "judging", [{"command": "agentic-maker check predicate --findings %s --trace %s --session %s" % (fl, os.path.join(newest["take_dir"], "trace.norm.jsonl"), session),
                                "why": "judge the fix against the rerun"} for fl in files]
        problems, _ = witness_problems(led, session)
        if not problems:
            return "closing", [{"command": "agentic-maker ledger close --session %s --outcome clean --reason \"<what changed and what proved it>\"" % session, "why": "every fix is witnessed"}]
    if not reads:
        return "reading", [{"delegate": "trace-reader", "input": os.path.join(newest["take_dir"], "trace.md"),
                            "why": "spawn agentic-maker:trace-reader with the absolute paths of this take; its findings are recorded when it stops"}]
    last = reads[-1]
    done = {f.get("id") for f in led.get("findings", {}).values() if f.get("findings_file") == last.get("findings_file")}
    todo = [i for i in last.get("verified_ids", []) if i not in done]
    if todo:
        return "fixing", [{"command": "agentic-maker ledger fix %s --session %s --findings %s --trace %s" % (" ".join(todo), session, last["findings_file"], os.path.join(newest["take_dir"], "trace.norm.jsonl")),
                           "why": "keep a copy of the controlling file, then rewrite the text it names"}]
    problems, nxt = witness_problems(led, session)
    if not problems:
        return "closing", [{"command": "agentic-maker ledger close --session %s --outcome clean --reason \"<why>\"" % session, "why": "nothing left to fix and the receipts pass"}]
    return "closing", nxt or [{"command": "agentic-maker ledger close --session %s --outcome open --reason \"<what is left>\"" % session, "why": "report what is open"}]


def record_receipts(root, session, take_dir, receipts):
    led, p = load(root, session=session)
    for t in led["traces"]:
        if os.path.realpath(t["take_dir"]) == os.path.realpath(take_dir):
            t["receipts"] = receipts
    save(led, p)


def fixing_ids(root, session, findings_path):
    led, _ = load(root, session=session)
    rel = os.path.relpath(os.path.abspath(findings_path if os.path.isabs(findings_path) else os.path.join(root, findings_path)), root)
    return [f["id"] for f in led.get("findings", {}).values() if f.get("findings_file") == rel and f.get("status") == "fixing"]


def record_predicates(root, session, findings_path, trace_norm, results):
    """The verdict of a rerun, kept against the fix it judges: `ledger close --outcome clean` reads these."""
    led, p = load(root, session=session)
    take_dir = os.path.dirname(os.path.abspath(trace_norm))
    take = next((t for t in led["traces"] if os.path.realpath(t["take_dir"]) == os.path.realpath(take_dir)), None)
    for r in results:
        key = fkey(root, findings_path, r["id"])
        if key in led["findings"]:
            led["findings"][key]["predicate"] = {"passed": r["passed"], "detail": r.get("detail"), "take_dir": take_dir,
                                                 "take_epoch": (take or {}).get("finished_epoch", 0), "at": now_iso()}
    save(led, p)


def judge(root, session, findings_path, fid, passed, reason):
    """The orchestrator's own verdict when a predicate cannot decide (type `judged`, or a predicate that tested the wrong thing): kept with its reason."""
    led, p = load(root, session=session)
    key = fkey(root, findings_path, fid)
    f = led["findings"].get(key)
    if not f:
        raise CliError("not_found", "finding_not_in_ledger", "%s is not being fixed in this ledger" % key,
                       suggestion="agentic-maker ledger fix %s --session %s --findings %s --trace <trace.norm.jsonl>" % (fid, session, findings_path))
    newest = _newest_trace(led)
    if not newest or newest.get("finished_epoch", 0) <= f.get("fix_epoch", 0):
        raise CliError("conflict", "no_rerun_yet", "no run has finished since the fix to %s: there is nothing to judge it by" % fid,
                       suggestion="agentic-maker run %s --session %s" % ((newest or {}).get("scenario") or "<scenario>", session))
    f["predicate"] = {"passed": bool(passed), "judged": reason, "take_dir": newest["take_dir"], "take_epoch": newest.get("finished_epoch", 0), "at": now_iso()}
    event(led, "judge", finding=key, passed=bool(passed), reason=reason)
    save(led, p)
    return f


def refuse_if_stale_bin(root, session, bin_path):
    """A rerun of a built CLI that tests the binary from before the fix reads as a false clean."""
    try:
        led, _ = load(root, session=session)
    except CliError:
        return
    if not bin_path or not os.path.exists(bin_path) or _covered(os.path.abspath(bin_path), led["targets"]):
        return            # a script that lives inside the target is its own source
    newest = newest_mtime(led["targets"])
    if newest > os.path.getmtime(bin_path) + 1.0:
        raise CliError("conflict", "stale_bin", "the built binary %s is older than the sources in the ledger's targets: the run would test the code from before the fix" % bin_path,
                       suggestion="rebuild it (the scenario's `build:` line says how), then run again")


READER_TYPE = "agentic-maker:trace-reader"


def _take_from_brief(transcript_path):
    """The reader's first message lists absolute paths; the one ending in trace.norm.jsonl names the take."""
    try:
        with open(transcript_path, encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                if i > 40:
                    break
                m = re.search(r"(/[^\s\"'`\\]+/trace\.norm\.jsonl)", line)
                if m and os.path.isfile(m.group(1)):
                    return os.path.dirname(m.group(1))
    except OSError:
        pass
    return None


def _reader_tokens(transcript_path):
    """Tokens the reader used, one count per API response (a response is written once per content block)."""
    by_msg = {}
    try:
        with open(transcript_path, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                m = r.get("message") if isinstance(r, dict) else None
                if r.get("type") == "assistant" and isinstance(m, dict) and isinstance(m.get("usage"), dict):
                    by_msg[m.get("id") or len(by_msg)] = m["usage"]
    except OSError:
        return None
    tot = {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0}
    for u in by_msg.values():
        tot["input"] += u.get("input_tokens", 0) or 0
        tot["output"] += u.get("output_tokens", 0) or 0
        tot["cache_read"] += u.get("cache_read_input_tokens", 0) or 0
        tot["cache_create"] += u.get("cache_creation_input_tokens", 0) or 0
    return tot


def _json_reply(text):
    """The reader's final message should be one JSON object; tolerate a code fence around it."""
    t = (text or "").strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\s*", "", t)
        t = re.sub(r"\s*```\s*$", "", t)
    try:
        d = json.loads(t)
        return d if isinstance(d, (dict, list)) else None
    except ValueError:
        return None


def reader_done(stdin_text, env=None):
    """SubagentStop hook for the reader: the reply is saved exactly as written, checked, and sent back once if a quote does not verify. Never raises."""
    env = env if env is not None else os.environ
    try:
        if env.get("AGENTIC_MAKER_HOOKS", "").lower() == "off" or not stdin_text.strip():
            return 0, ""
        pl = json.loads(stdin_text)
        if pl.get("agent_type") != READER_TYPE or not pl.get("session_id"):
            return 0, ""
        root, ptr = _find_pointer(pl["session_id"], [pl.get("cwd"), env.get("CLAUDE_PROJECT_DIR")])
        if not ptr:
            return 0, ""
        led_path = read_json(ptr)["ledger"]
        led = read_json(led_path)
        if led["status"] in PASS_STATUSES:
            return 0, ""
        take = _take_from_brief(pl.get("agent_transcript_path") or "")
        if not take:
            return 0, ""
        from agentic_maker import check as check_mod
        again = bool(pl.get("stop_hook_active"))
        fdir = os.path.join(take, "findings")
        os.makedirs(fdir, exist_ok=True)
        n = 1 + len([x for x in os.listdir(fdir) if re.match(r"^\d+\.json$", x)])
        msg = pl.get("last_assistant_message") or ""
        data = _json_reply(msg)
        if data is None:
            with open(os.path.join(fdir, "%d.invalid.txt" % n), "w", encoding="utf-8") as f:
                f.write(msg)
            if not again:
                return 0, json.dumps({"decision": "block", "reason": "Your final message must be exactly one JSON object ({\"findings\": [...], \"nice\": [...], \"dimensions_clear\": [...]}) and nothing else: no prose before or after. Return it again."})
            verified, rejected, fpath = [], {"reply": ["not a JSON object"]}, None
        else:
            fpath = os.path.join(fdir, "%d.json" % n)
            write_json(fpath, data)
            chk = check_mod.check_findings(fpath, os.path.join(take, "trace.norm.jsonl"), root)
            rejected = {r["id"]: r["problems"] for r in chk["results"] if not r["verified"]}
            if rejected and not again:
                lines = ["%s: %s" % (i, "; ".join(p)) for i, p in rejected.items()]
                return 0, json.dumps({"decision": "block", "reason": "These findings did not verify against the trace:\n" + "\n".join(lines) +
                                      "\nReturn the complete JSON object again with those fixed: a quote is copied exactly from the cited event, trace_refs name events that exist. Findings that verified stay as they are."})
            verified = chk["verified_ids"]
            write_json(os.path.join(fdir, "%d.verified.json" % n), {"verified_ids": verified})
        led = read_json(led_path)
        led.setdefault("reads", []).append({
            "take_dir": take, "findings_file": os.path.relpath(fpath, root) if fpath else None, "verified_ids": verified, "rejected": rejected,
            "reader_tokens": _reader_tokens(pl.get("agent_transcript_path") or ""), "agent_id": pl.get("agent_id"), "at": now_iso()})
        event(led, "read", take_dir=take, verified=len(verified), rejected=len(rejected))
        save(led, led_path)
        return 0, ""
    except Exception as e:  # never trap the agent
        sys.stderr.write("agentic-maker reader-done: ignored internal error: %s\n" % e)
        return 0, ""


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
