"""Turn a derailment scenario into a `claude plugin eval` case: derailment finds, the eval guards in CI.

Written: prompt.md (the prompt, turn limit, tools), graders/skill-fired.md (the target was chosen by name - the trigger
check), a grader per receipt that eval can express (exists, regex), and fixture.sh + case.yaml when the scenario seeds
files. Receipts that eval has no grader for (cmd, json, mtime-in-window, unchanged, no-extra-files) are listed, not dropped.
"""
import os
import re

from agentic_maker import scenario as sc_mod
from agentic_maker.common import slug
from agentic_maker.envelope import CliError

SMALL = 20000
READ_ONLY = {"Read", "Glob", "Grep", "Skill", "Agent"}


def _q2(t):
    return '"%s"' % t if re.search(r"[ ()*]", t) else t


def _skill_names(target_dir):
    names = []
    for dp, _, fns in os.walk(target_dir):
        if "SKILL.md" in fns:
            m = re.search(r"^name:\s*(.+?)\s*$", open(os.path.join(dp, "SKILL.md"), encoding="utf-8").read(), re.M)
            names.append(m.group(1) if m else os.path.basename(dp))
    return names


def _q(s):
    return "'" + s.replace("'", "''") + "'"


def emit(root, sc, out_dir):
    meta = sc["meta"]
    case = os.path.join(out_dir, slug(meta["name"]))
    os.makedirs(os.path.join(case, "graders"), exist_ok=True)
    written, skipped, warns = [], [], []
    tools = meta.get("allowed_tools") or ["Read", "Glob", "Grep", "Skill"]
    with open(os.path.join(case, "prompt.md"), "w", encoding="utf-8") as f:
        f.write("---\nmax_turns: %d\ntimeout_seconds: %d\nallowed_tools: [%s]\n---\n\n%s\n" % (
            min(int(meta["max_turns"]), 40), int(meta["timeout_s"]), ", ".join(tools), sc["sections"]["prompt"]))
    written.append("prompt.md")
    if meta["kind"] in ("skill", "plugin"):
        t = meta["target"] if os.path.isabs(meta["target"]) else os.path.join(root, meta["target"])
        names = _skill_names(t) if os.path.isdir(t) else []
        if names:
            alt = "|".join(re.escape(n) for n in names)
            with open(os.path.join(case, "graders", "skill-fired.md"), "w", encoding="utf-8") as f:
                f.write("---\ntype: tool_used\ntool: Skill\ninput_match: %s\n---\n" % _q(r'"skill"\s*:\s*"(?:[\w-]+:)?(?:%s)"' % alt))
            written.append("graders/skill-fired.md")
        else:
            warns.append("no SKILL.md found under the target: no trigger grader written")
    copies, _ = sc_mod.fixture_steps(sc)
    seeded = {(d or os.path.basename(s.rstrip("/"))) for s, d in copies}
    n = 0
    for r in sc_mod.receipt_specs(sc):
        kind, spec = r["kind"], r["spec"]
        if kind == "exists" and spec not in seeded:
            n += 1
            with open(os.path.join(case, "graders", "receipt-%d-exists.md" % n), "w", encoding="utf-8") as f:
                f.write("---\ntype: file_exists\npath: %s\n---\n" % _q(spec))
            written.append("graders/receipt-%d-exists.md" % n)
        elif kind == "regex":
            m = re.match(r"^(\S+)\s+/(.*)/([imsx]*)$", spec)
            if m:
                n += 1
                flags = "".join(c for c in m.group(3) if c in "ims")
                with open(os.path.join(case, "graders", "receipt-%d-regex.md" % n), "w", encoding="utf-8") as f:
                    f.write("---\ntype: regex\ntarget:\n  source: file\n  path: %s\npattern: %s\n%s---\n" % (_q(m.group(1)), _q(m.group(2)), ("flags: %s\n" % flags) if flags else ""))
                written.append("graders/receipt-%d-regex.md" % n)
            else:
                skipped.append(r["line"])
        else:
            skipped.append(r["line"])
    if copies:
        lines = ["#!/bin/sh", "set -e"]
        for src, dest in copies:
            s = src if os.path.isabs(src) else os.path.join(root, src)
            d = dest or os.path.basename(s.rstrip("/"))
            files = [s] if os.path.isfile(s) else [os.path.join(dp, fn) for dp, _, fns in os.walk(s) for fn in fns] if os.path.isdir(s) else []
            if not files:
                warns.append("fixture not found: %s" % src)
            for fp in files:
                if os.path.getsize(fp) > SMALL:
                    warns.append("fixture %s is over %d bytes: add it to the case by hand" % (fp, SMALL))
                    continue
                rel = d if fp == s else os.path.join(d, os.path.relpath(fp, s))
                text = open(fp, encoding="utf-8", errors="replace").read()
                tag = "AM_EOF"
                lines += ['mkdir -p "$(dirname %s)"' % _q(rel), "cat > %s <<'%s'" % (_q(rel), tag), text.rstrip("\n"), tag]
        script = os.path.join(case, "fixture.sh")
        with open(script, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        os.chmod(script, 0o755)
        with open(os.path.join(case, "case.yaml"), "w", encoding="utf-8") as f:
            f.write('schema_version: "1.1"\nname: %s\ncontext:\n  scaffold_script: fixture.sh\n' % slug(meta["name"]))
        written += ["fixture.sh", "case.yaml"]
    return {"case_dir": case, "written": written, "receipts_not_expressible": skipped, "warnings": warns,
            "run_with": "claude plugin eval <plugin dir> --scaffold --case %s --runs 1%s" % (
                slug(meta["name"]), (" --allow-tools " + " ".join(_q2(t) for t in tools if t not in READ_ONLY)) if [t for t in tools if t not in READ_ONLY] else "")}
