#!/usr/bin/env python3
"""Shape and size checks for reference files (docs/migration-brief.md, "File rules").

Usage: lint-refs.py [path ...]   (default: every .md under skills/*/references)
Exit 0 clean, 1 violations. Python 3.9+, stdlib only.
"""
import os
import re
import sys

SOFT, HARD = 8192, 10240
FENCE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})")
MARKER = re.compile(r"<!--\s*src:\s*(.*?)\s*-->", re.S)
PERSONAL = re.compile(r"/Users/|@gmail\.|ghp_[A-Za-z0-9]{10,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{12,}")


def files(args, root):
    if args:
        return [a for a in args if a.endswith(".md")]
    out = []
    for dp, _, fns in os.walk(os.path.join(root, "skills")):
        if "/references" in dp or dp.endswith("references"):
            out += [os.path.join(dp, f) for f in fns if f.endswith(".md")]
    return sorted(out)


def lint(path):
    errs = []
    raw = open(path, encoding="utf-8").read()
    size = len(raw.encode("utf-8"))
    if size > HARD:
        errs.append("size %d > hard cap %d" % (size, HARD))
    elif size > SOFT:
        errs.append("size %d > %d (split by decision)" % (size, SOFT))
    lines = raw.splitlines()
    body = lines
    if "/fresh/" in path.replace(os.sep, "/"):
        if not (lines and lines[0] == "---" and "---" in lines[1:6]):
            errs.append("fresh/ file needs front matter with as_of and verify_before_citing")
        else:
            end = lines.index("---", 1)
            head = "\n".join(lines[1:end])
            if "as_of:" not in head or "verify_before_citing:" not in head:
                errs.append("fresh/ front matter lacks as_of or verify_before_citing")
            elif re.search(r"^as_of:\s*(unknown|)\s*$", head, re.M):
                errs.append("fresh/ as_of must be a date (YYYY, YYYY-MM or YYYY-MM-DD), not unknown")
            body = lines[end + 1:]
    nonblank = [l for l in body if l.strip()]
    if not nonblank or not nonblank[0].startswith("# "):
        errs.append("first line must be '# Title'")
    if not any(l.startswith("> Read when:") for l in nonblank[:3]):
        errs.append("missing '> Read when: ...' line right after the title")
    fence = None
    for i, l in enumerate(lines, 1):
        m = FENCE.match(l)
        if m:
            tok = m.group(1)
            if fence is None:
                fence = (tok[0], len(tok))
            elif tok[0] == fence[0] and len(tok) >= fence[1] and l.strip() == tok:
                fence = None
    if fence is not None:
        errs.append("unbalanced code fence")
    infence = None
    for i, l in enumerate(lines, 1):                  # an empty code span ("relative to ``.") is a path that went missing
        m = FENCE.match(l)
        if m:
            tok = m.group(1)
            infence = None if (infence and tok[0] == infence[0] and len(tok) >= infence[1] and l.strip() == tok) else (infence or (tok[0], len(tok)))
            continue
        if infence is None and l.count("``") == 1 and re.search(r"(?<!`)``(?!`)[.,;:)]", l):
            errs.append("line %d: empty code span (``) followed by punctuation" % i)
    for m in MARKER.finditer(raw):
        for k in m.group(1).split("|"):
            if "#" not in k:
                errs.append("marker without '#heading': %r" % k.strip())
    if PERSONAL.search(raw):
        errs.append("personal path/email/token pattern")
    return errs


def main(argv):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bad = 0
    fl = files(argv, root)
    for p in fl:
        for e in lint(p):
            bad += 1
            print("%s: %s" % (os.path.relpath(p, root) if os.path.isabs(p) else p, e))
    print("lint-refs: %d files, %d violations" % (len(fl), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
