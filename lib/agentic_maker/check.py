"""Deterministic gates between a claim and the next step.

receipts  did the run leave the world in the state the scenario says it must? (anti-self-report)
findings  are the reader's findings real? every quote must appear verbatim in the cited trace events
diff      did the applied edit fix the cause, or only bolt a rule next to the unchanged cause?
nice      did an edit remove text a [NICE] behaviour depended on?
"""
import fnmatch
import json
import os
import re
import subprocess

from agentic_maker import scenario as sc_mod
from agentic_maker import trace as trace_mod
from agentic_maker.common import norm_ws, read_json, sha256_file, write_json
from agentic_maker.envelope import CliError

CODES = set(
    ["S%d" % i for i in range(1, 6)] + ["M%d" % i for i in range(1, 8)] + ["O%d" % i for i in range(1, 9)] +
    ["C%d" % i for i in range(1, 6)] + ["T1", "T2", "T3"])
MARKERS = {"STUCK", "BROKE", "GUESSED", "NICE"}
SEVERITIES = {"P0", "P1", "P2"}
LAYERS = {"trigger", "discovery", "execution", "recovery", "completion"}
FIX_KINDS = {"rewrite", "delete", "inline-at-point-of-use", "restructure", "add-probe", "add"}
BELIEF_SOURCES = {"observed", "inferred"}
PREDICATE_FIELDS = {
    "tool_used": ("tool",), "regex": ("pattern",), "not_regex": ("pattern",), "order": ("before", "after"),
    "reads_file": ("path",), "exit_code": ("command", "equals"), "judged": ("criteria",),
}
IMPERATIVE = re.compile(r"\b(always|never|don'?t|do not|must|make sure|important|ensure|remember|should)\b", re.I)


# ---------------------------------------------------------------- receipts
def _rel(ws, p):
    full = os.path.abspath(os.path.join(ws, p))
    if not (full == ws or full.startswith(ws + os.sep)):
        raise CliError("validation", "receipt_path_escapes", "receipt path leaves the workspace: %s" % p)
    return full


def _dotted(obj, path):
    cur = obj
    for part in [p for p in path.replace("[", ".").replace("]", "").split(".") if p != "" and p != "$"]:
        if isinstance(cur, list):
            cur = cur[int(part)]
        elif isinstance(cur, dict):
            cur = cur[part]
        else:
            raise KeyError(part)
    return cur


def _walk_files(ws):
    out = []
    for dp, dns, fns in os.walk(ws):
        dns[:] = [d for d in dns if d != ".am-bin"]
        for fn in fns:
            out.append(os.path.relpath(os.path.join(dp, fn), ws))
    return out


def _one_receipt(r, ws, run):
    kind, spec = r["kind"], r["spec"]
    try:
        if kind == "exists":
            ok = os.path.exists(_rel(ws, spec))
            return ok, "exists" if ok else "missing: %s" % spec
        if kind == "absent":
            ok = not os.path.exists(_rel(ws, spec))
            return ok, "absent" if ok else "present: %s" % spec
        if kind == "nonempty":
            p = _rel(ws, spec)
            ok = os.path.isfile(p) and os.path.getsize(p) > 0
            return ok, ("%d bytes" % os.path.getsize(p)) if ok else "missing or empty: %s" % spec
        if kind == "type":
            path, want = spec.rsplit(None, 1)
            p = _rel(ws, path)
            raw = open(p, "rb").read()
            if want == "json":
                json.loads(raw.decode("utf-8"))
            elif want == "utf8":
                raw.decode("utf-8")
            else:
                return False, "unknown type %r (json|utf8)" % want
            return True, "parses as %s" % want
        if kind == "json":
            m = re.match(r"^(\S+)\s+(\S+)\s*(==|!=|exists)?\s*(.*)$", spec)
            path, key, op, val = m.group(1), m.group(2), m.group(3) or "exists", m.group(4)
            data = json.load(open(_rel(ws, path), encoding="utf-8"))
            got = _dotted(data, key)
            if op == "exists":
                return True, "found %s" % key
            try:
                want = json.loads(val)
            except ValueError:
                want = val
            ok = (got == want) if op == "==" else (got != want)
            return ok, "%s = %r" % (key, got)
        if kind == "regex":
            m = re.match(r"^(\S+)\s+/(.*)/([imsx]*)$", spec)
            flags = sum({"i": re.I, "m": re.M, "s": re.S, "x": re.X}[c] for c in m.group(3))
            text = open(_rel(ws, m.group(1)), encoding="utf-8", errors="replace").read()
            ok = re.search(m.group(2), text, flags) is not None
            return ok, "matched" if ok else "no match for /%s/" % m.group(2)
        if kind == "cmd":
            cmd, _, code = spec.partition("=>")
            want = int(code.strip() or 0)
            env = {"PATH": os.path.join(ws, ".am-bin") + os.pathsep + os.environ.get("PATH", ""), "HOME": ws}
            res = subprocess.run(["/bin/sh", "-c", cmd.strip()], cwd=ws, env=env, capture_output=True, text=True, timeout=30)
            return res.returncode == want, "exit %d (wanted %d)%s" % (res.returncode, want, (": " + res.stderr.strip()[:120]) if res.returncode != want else "")
        if kind == "mtime-in-window":
            p = _rel(ws, spec)
            if not os.path.exists(p):
                return False, "missing: %s" % spec
            m = os.path.getmtime(p)
            lo, hi = run.get("started_at_epoch", 0) - 2, run.get("finished_at_epoch", 0) + 2
            return lo <= m <= hi, "mtime inside the run window" if lo <= m <= hi else "mtime outside the run window (stale file?)"
        if kind == "unchanged":
            p = _rel(ws, spec)
            want = (run.get("seed_manifest") or {}).get(os.path.relpath(p, ws))
            if want is None:
                return False, "not in the seed manifest (nothing to compare)"
            ok = os.path.exists(p) and sha256_file(p) == want
            return ok, "identical to the seeded file" if ok else "changed or removed"
        if kind == "no-extra-files":
            parts = spec.split()
            base = parts[0] if parts else "."
            allow = []
            for tok in parts[1:]:
                if tok.startswith("allow="):
                    allow = [a for a in tok[6:].split(",") if a]
            seed = set((run.get("seed_manifest") or {}).keys())
            extra = []
            for f in _walk_files(_rel(ws, base)):
                rel = os.path.normpath(os.path.join(base, f))
                if rel in seed or any(fnmatch.fnmatch(rel, a) for a in allow):
                    continue
                extra.append(rel)
            return not extra, "no unexpected files" if not extra else "unexpected: %s" % ", ".join(sorted(extra)[:8])
    except CliError:
        raise
    except Exception as e:  # a malformed receipt is a failed receipt with the reason, not a crash
        return False, "%s: %s" % (type(e).__name__, e)
    return False, "unknown receipt kind %r" % kind


def check_receipts(take_dir, workspace=None):
    take_dir = os.path.abspath(take_dir)
    run = read_json(os.path.join(take_dir, "run.json"))
    sc = sc_mod.parse(run["scenario_file"])
    ws = os.path.realpath(workspace or run.get("workspace") or "")
    if not ws or not os.path.isdir(ws):
        raise CliError("not_found", "workspace_missing", "the run's workspace is gone or was never recorded: %r" % ws,
                       suggestion="pass --workspace <dir> to check an existing directory")
    specs = sc_mod.receipt_specs(sc)
    results = []
    for r in specs:
        ok, detail = _one_receipt(r, ws, run)
        results.append({"kind": r["kind"], "spec": r["spec"], "ok": bool(ok), "detail": detail})
    passed = sum(1 for r in results if r["ok"])
    out = {"take_dir": take_dir, "workspace": ws, "total": len(results), "passed": passed, "failed": len(results) - passed, "receipts": results}
    write_json(os.path.join(take_dir, "receipts.json"), out)
    return out


# ---------------------------------------------------------------- findings
def _event_text(rec):
    parts = [rec.get("text") or "", rec.get("name") or ""]
    if rec.get("args") is not None:
        parts.append(json.dumps(rec["args"], ensure_ascii=False))
    return norm_ws(" ".join(parts))


def _in_events(quote, refs, norm):
    q = norm_ws(quote)
    if not q:
        return False
    return any(q in _event_text(norm[r]) for r in refs if r in norm)


def _predicate_problems(p):
    if not isinstance(p, dict) or p.get("type") not in PREDICATE_FIELDS:
        return ["rerun_predicate.type must be one of %s" % "|".join(sorted(PREDICATE_FIELDS))]
    return ["rerun_predicate.%s missing" % f for f in PREDICATE_FIELDS[p["type"]] if p.get(f) in (None, "")]


def verify_finding(f, norm, root):
    probs = []
    if not isinstance(f, dict):
        return ["finding is not an object"]
    for k in ("id", "quote", "belief"):
        if not isinstance(f.get(k), str) or not f.get(k).strip():
            probs.append("`%s` must be a non-empty string" % k)
    if f.get("marker") not in MARKERS:
        probs.append("marker must be one of %s" % "|".join(sorted(MARKERS)))
    if f.get("severity") not in SEVERITIES:
        probs.append("severity must be P0|P1|P2")
    if f.get("root_code") not in CODES:
        probs.append("root_code %r is not in the taxonomy" % f.get("root_code"))
    if f.get("layer") not in LAYERS:
        probs.append("layer must be one of %s" % "|".join(sorted(LAYERS)))
    if f.get("belief_source") not in BELIEF_SOURCES:
        probs.append("belief_source must be observed|inferred")
    refs = f.get("trace_refs")
    if not (isinstance(refs, list) and refs and all(isinstance(r, int) for r in refs)):
        probs.append("trace_refs must be a non-empty list of event numbers")
        refs = []
    missing = [r for r in refs if r not in norm]
    if missing:
        probs.append("trace_refs %s do not exist in the trace" % missing)
    elif refs and isinstance(f.get("quote"), str) and f["quote"].strip() and not _in_events(f["quote"], refs, norm):
        probs.append("quote does not appear verbatim in the cited events %s" % refs)
    if f.get("belief_source") == "observed" and refs:
        if not any(norm[r]["kind"] == "thinking" and (norm[r].get("text") or "").strip() for r in refs if r in norm):
            probs.append("belief_source=observed but no cited event carries thinking text; use inferred")
    ct = f.get("controlling_text")
    if not isinstance(ct, dict) or not ct.get("file") or not isinstance(ct.get("quote"), str) or not ct.get("quote").strip():
        probs.append("controlling_text needs {file, quote} (quote may be the literal string ABSENT)")
    elif ct["quote"] != "ABSENT":
        p = ct["file"] if os.path.isabs(ct["file"]) else os.path.join(root, ct["file"])
        if not os.path.isfile(p):
            probs.append("controlling_text.file does not exist: %s" % ct["file"])
        elif norm_ws(ct["quote"]) not in norm_ws(open(p, encoding="utf-8", errors="replace").read()):
            probs.append("controlling_text.quote is not in %s (verbatim)" % ct["file"])
    fx = f.get("fix")
    if not isinstance(fx, dict) or fx.get("kind") not in FIX_KINDS or not isinstance(fx.get("patch"), str) or not fx.get("patch").strip():
        probs.append("fix needs {kind: %s, patch}" % "|".join(sorted(FIX_KINDS)))
    probs += _predicate_problems(f.get("rerun_predicate"))
    return probs


def check_findings(findings_path, trace_norm, root):
    data = read_json(findings_path)
    items = data.get("findings") if isinstance(data, dict) else data
    nice = data.get("nice", []) if isinstance(data, dict) else []
    if not isinstance(items, list):
        raise CliError("validation", "findings_shape", "%s: expected {\"findings\": [...]} or a list" % findings_path)
    norm = trace_mod.load_norm(trace_norm)
    seen, out = set(), []
    for f in items:
        probs = verify_finding(f, norm, root)
        fid = f.get("id") if isinstance(f, dict) else None
        if fid in seen:
            probs.append("duplicate id %r" % fid)
        seen.add(fid)
        out.append({"id": fid, "verified": not probs, "problems": probs})
    nice_out = []
    for n in nice:
        refs = n.get("trace_refs") if isinstance(n, dict) else None
        ok = bool(isinstance(n, dict) and refs and isinstance(n.get("quote"), str) and _in_events(n["quote"], refs, norm))
        nice_out.append({"quote": (n.get("quote") if isinstance(n, dict) else None), "verified": ok})
    verified = [o["id"] for o in out if o["verified"]]
    return {"findings_file": findings_path, "total": len(out), "verified": len(verified), "rejected": len(out) - len(verified),
            "verified_ids": verified, "results": out, "nice": nice_out}


# ---------------------------------------------------------------- diff and nice
def _git(root, *args):
    try:
        r = subprocess.run(["git", "-C", root] + list(args), capture_output=True, text=True, timeout=30)
    except FileNotFoundError:
        raise CliError("not_found", "git_missing", "git is needed for `check diff`")
    if r.returncode != 0:
        raise CliError("validation", "git_failed", "git %s failed: %s" % (" ".join(args), r.stderr.strip()[:200]),
                       suggestion="run inside a git work tree; commit or stage the target before the first fix so the diff has a base")
    return r.stdout


def _hunks(diff_text):
    added, removed = [], []
    for ln in diff_text.splitlines():
        if ln.startswith("+++") or ln.startswith("---"):
            continue
        if ln.startswith("+"):
            added.append(ln[1:])
        elif ln.startswith("-"):
            removed.append(ln[1:])
    return added, removed


def _finding(findings_path, fid):
    data = read_json(findings_path)
    items = data.get("findings") if isinstance(data, dict) else data
    for f in items or []:
        if isinstance(f, dict) and f.get("id") == fid:
            return f
    raise CliError("not_found", "finding_not_found", "no finding %r in %s" % (fid, findings_path))


def check_diff(findings_path, fid, root, base="HEAD", justify=None):
    f = _finding(findings_path, fid)
    ct = f.get("controlling_text") or {}
    rel = ct.get("file")
    if not rel:
        raise CliError("validation", "no_controlling_file", "finding %s has no controlling_text.file" % fid)
    diff = _git(root, "diff", "-U0", base, "--", rel)
    if not diff.strip():
        return {"verdict": "no_change", "finding": fid, "file": rel, "reason": "no change to %s since %s" % (rel, base)}
    added, removed = _hunks(diff)
    path = rel if os.path.isabs(rel) else os.path.join(root, rel)
    now = norm_ws(open(path, encoding="utf-8", errors="replace").read())
    if ct.get("quote") == "ABSENT":
        return {"verdict": "ok", "finding": fid, "file": rel, "reason": "the cause was an absence; an addition is the fix",
                "added_lines": len(added), "removed_lines": len(removed)}
    still = norm_ws(ct.get("quote", "")) in now
    imperative = [a for a in added if IMPERATIVE.search(a)]
    if not still:
        return {"verdict": "ok", "finding": fid, "file": rel, "reason": "the quoted controlling text was rewritten or deleted",
                "added_lines": len(added), "removed_lines": len(removed)}
    if imperative and not removed:
        res = {"verdict": "flag", "finding": fid, "file": rel, "rule": "patch-by-rule",
               "reason": "the controlling text is unchanged and the edit only adds imperative text (%d line(s)): the agent will still read the misleading text first" % len(imperative),
               "evidence": imperative[:3], "added_lines": len(added), "removed_lines": len(removed)}
        if justify:
            res["verdict"], res["justification"] = "ok", justify
        return res
    return {"verdict": "ok", "finding": fid, "file": rel, "note": "controlling text unchanged; the added text is descriptive, not a rule",
            "added_lines": len(added), "removed_lines": len(removed)}


def check_nice(findings_path, root):
    data = read_json(findings_path)
    nice = data.get("nice", []) if isinstance(data, dict) else []
    out = []
    for n in nice:
        ct = (n or {}).get("controlling_text") or {}
        if not ct.get("file") or not ct.get("quote") or ct.get("quote") == "ABSENT":
            out.append({"quote": n.get("quote"), "status": "unguarded", "reason": "no controlling_text to guard"})
            continue
        p = ct["file"] if os.path.isabs(ct["file"]) else os.path.join(root, ct["file"])
        present = os.path.isfile(p) and norm_ws(ct["quote"]) in norm_ws(open(p, encoding="utf-8", errors="replace").read())
        if present:
            out.append({"quote": n.get("quote"), "status": "intact"})
        elif n.get("superseded_by"):
            out.append({"quote": n.get("quote"), "status": "superseded", "by": n["superseded_by"]})
        else:
            out.append({"quote": n.get("quote"), "status": "REMOVED", "file": ct["file"],
                        "reason": "text a good behaviour depended on is gone and no finding supersedes it"})
    return {"nice": out, "removed": [o for o in out if o["status"] == "REMOVED"]}


# ---------------------------------------------------------------- rerun predicates
def _calls(norm):
    return [r for r in sorted(norm.values(), key=lambda r: r["n"]) if r["kind"] == "tool_use"]


def _call_matches(r, spec):
    if isinstance(spec, str):
        spec = {"tool": spec}
    if r.get("name") != spec.get("tool"):
        return False
    im = spec.get("input_match")
    return re.search(im, json.dumps(r.get("args"), ensure_ascii=False)) is not None if im else True


def eval_predicate(pred, norm):
    """Judge one rerun_predicate against a new trace. Returns {passed: True|False|None, detail}."""
    t = pred.get("type")
    recs = sorted(norm.values(), key=lambda r: r["n"])
    blob = "\n".join("%s %s" % (r.get("text") or "", json.dumps(r.get("args"), ensure_ascii=False) if r.get("args") else "") for r in recs)
    if t == "tool_used":
        n = sum(1 for r in _calls(norm) if _call_matches(r, pred))
        return {"passed": n >= 1, "detail": "%d matching call(s)" % n}
    if t == "regex":
        ok = re.search(pred["pattern"], blob, re.S) is not None
        return {"passed": ok, "detail": "pattern %s" % ("found" if ok else "not found")}
    if t == "not_regex":
        ok = re.search(pred["pattern"], blob, re.S) is None
        return {"passed": ok, "detail": "pattern %s" % ("absent" if ok else "present")}
    if t == "order":
        idx = {}
        for key in ("before", "after"):
            idx[key] = next((r["n"] for r in _calls(norm) if _call_matches(r, pred[key])), None)
        ok = idx["before"] is not None and idx["after"] is not None and idx["before"] < idx["after"]
        return {"passed": ok, "detail": "before at %s, after at %s" % (idx["before"], idx["after"])}
    if t == "reads_file":
        hit = [r["n"] for r in _calls(norm) if r.get("name") in ("Read", "Bash", "Grep", "Glob") and pred["path"] in json.dumps(r.get("args"))]
        return {"passed": bool(hit), "detail": "opened at event(s) %s" % hit if hit else "never opened"}
    if t == "exit_code":
        by_id = {r["tool_use_id"]: r for r in _calls(norm)}
        for r in recs:
            if r["kind"] == "tool_result" and r.get("tool_use_id") in by_id:
                if pred["command"] in json.dumps(by_id[r["tool_use_id"]].get("args")):
                    got = r.get("exit") if r.get("exit") is not None else (1 if r.get("is_error") else 0)
                    return {"passed": got == int(pred["equals"]), "detail": "exit %s" % got}
        return {"passed": False, "detail": "no matching command in the trace"}
    if t == "judged":
        return {"passed": None, "detail": "needs a judge: %s" % pred.get("criteria")}
    return {"passed": False, "detail": "unknown predicate type %r" % t}


def check_predicates(findings_path, trace_norm, ids=None):
    data = read_json(findings_path)
    items = data.get("findings") if isinstance(data, dict) else data
    norm = trace_mod.load_norm(trace_norm)
    out = []
    for f in items or []:
        if ids and f.get("id") not in ids:
            continue
        res = eval_predicate(f.get("rerun_predicate") or {}, norm)
        out.append(dict(res, id=f.get("id"), type=(f.get("rerun_predicate") or {}).get("type")))
    passed = sum(1 for o in out if o["passed"] is True)
    return {"results": out, "passed": passed, "failed": sum(1 for o in out if o["passed"] is False),
            "needs_judgement": sum(1 for o in out if o["passed"] is None), "total": len(out)}
