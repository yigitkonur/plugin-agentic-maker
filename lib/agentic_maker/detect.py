"""Find the agent-facing surfaces in a project: skills, plugins, MCP servers, CLIs and scripts.

Locates only. Whether a candidate is good is judged by probing it (probe cli / probe mcp) and by reading it.
The rules are data (data/surfaces.tsv): a new ecosystem is a new row.
"""
import fnmatch
import os
import re

SKIP_DIRS = {".git", "node_modules", "target", "vendor", "__pycache__", ".venv", "venv", "dist", "build", ".agentic-maker", ".next"}
MAX_FILES = 6000
MAX_BYTES = 400000


def load_rules(path):
    rules = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            c = line.rstrip("\n").split("\t")
            while len(c) < 6:
                c.append("")
            rules.append({"kind": c[0], "eco": c[1], "how": c[2], "pattern": c[3], "scope": [s for s in c[4].split(",") if s], "note": c[5]})
    return rules


def detect(root, rules, kinds=None, evidence=3):
    cand = {}
    seen = 0

    def add(kind, eco, rel, line, note):
        key = (kind, eco, rel)
        e = cand.setdefault(key, {"kind": kind, "ecosystem": eco, "path": rel, "note": note, "evidence": []})
        if line and len(e["evidence"]) < evidence:
            e["evidence"].append(line)

    for dp, dns, fns in os.walk(root):
        dns[:] = sorted(d for d in dns if d not in SKIP_DIRS)
        for fn in sorted(fns):
            seen += 1
            if seen > MAX_FILES:
                break
            full = os.path.join(dp, fn)
            rel = os.path.relpath(full, root)
            text = None
            for r in rules:
                if kinds and r["kind"] not in kinds:
                    continue
                if r["how"] == "file":
                    pat = r["pattern"]
                    if (os.sep in pat and rel.endswith(pat)) or fn == pat:
                        add(r["kind"], r["eco"], os.path.dirname(rel) or ".", None, r["note"])
                elif r["how"] == "regex":
                    if r["scope"] and not any(fnmatch.fnmatch(fn, g) for g in r["scope"]):
                        continue
                    if text is None:
                        try:
                            if os.path.getsize(full) > MAX_BYTES:
                                text = ""
                            else:
                                text = open(full, encoding="utf-8", errors="replace").read()
                        except OSError:
                            text = ""
                    for n, ln in enumerate(text.splitlines(), 1):
                        if re.search(r["pattern"], ln):
                            add(r["kind"], r["eco"], rel, "%s:%d: %s" % (rel, n, ln.strip()[:120]), r["note"])
                elif r["how"] == "shebang":
                    try:
                        if os.access(full, os.X_OK) and os.path.getsize(full) < MAX_BYTES:
                            with open(full, "rb") as f:
                                first = f.readline(200).decode("utf-8", "replace")
                            if re.search(r["pattern"], first):
                                add(r["kind"], r["eco"], rel, None, r["note"])
                    except OSError:
                        pass
    out = sorted(cand.values(), key=lambda e: (e["kind"], e["path"]))
    return {"root": root, "candidates": out, "files_scanned": min(seen, MAX_FILES),
            "truncated": seen > MAX_FILES, "by_kind": {k: sum(1 for e in out if e["kind"] == k) for k in sorted({e["kind"] for e in out})}}
