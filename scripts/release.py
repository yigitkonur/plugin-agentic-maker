#!/usr/bin/env python3
"""Decide the next version of a Claude Code plugin repo from its commits, and write it everywhere it lives.

Usage: release.py [--root DIR] [--level auto|patch|minor|major] [--apply] [--notes-out FILE] [--github-output]
Dry run unless --apply. Python 3.9+, stdlib only; works on any plugin repo, so other repos can download this one file.

Why: Claude Code updates an installed plugin only when its `version` string changes, so every shipped change must
bump it, and the bump must reach every place the version is written.

Level (auto): commits since the last v*.*.* tag, merges and release commits left out.
  feat -> minor; fix, perf -> patch; `type!:` or "BREAKING CHANGE" -> major (minor while the major is 0).
  docs, ci, chore, test, style, build, refactor -> no release.
  A commit with no conventional prefix counts as a patch only if it changed a runtime path (skills/, agents/, hooks/,
  bin/, lib/, commands/, data/, .mcp.json, .lsp.json).
Writes: .claude-plugin/plugin.json, .claude-plugin/marketplace.json (every "version" equal to the old one), any
`__version__ = "old"` in lib/*/__init__.py, and CHANGELOG.md (an "## Unreleased" section is renamed; otherwise one is
generated from the commit subjects).
Exit 0 always on a clean decision (release or none); 2 on a repo it cannot read.
"""
import argparse
import datetime
import glob
import json
import os
import re
import subprocess
import sys

RUNTIME = ("skills/", "agents/", "hooks/", "bin/", "lib/", "commands/", "data/", ".mcp.json", ".lsp.json")
CONV = re.compile(r"^(?P<type>[a-zA-Z]+)(\([^)]*\))?(?P<bang>!)?:\s*(?P<subject>.+)$")
RANK = {"none": 0, "patch": 1, "minor": 2, "major": 3}
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def git(root, *args):
    r = subprocess.run(["git", "-C", root] + list(args), capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("release.py: git %s failed: %s" % (" ".join(args), r.stderr.strip()[:200]))
    return r.stdout


def current_version(root):
    p = os.path.join(root, ".claude-plugin", "plugin.json")
    if os.path.isfile(p):
        v = json.load(open(p, encoding="utf-8")).get("version")
        if v:
            return v
    m = os.path.join(root, ".claude-plugin", "marketplace.json")
    if os.path.isfile(m):
        d = json.load(open(m, encoding="utf-8"))
        for pl in d.get("plugins", []):
            if pl.get("version"):
                return pl["version"]
        if d.get("metadata", {}).get("version"):
            return d["metadata"]["version"]
    raise SystemExit("release.py: no version found in .claude-plugin/plugin.json or marketplace.json")


def commits_since(root):
    tags = git(root, "tag", "--list", "v[0-9]*.[0-9]*.[0-9]*", "--sort=-v:refname").split()
    base = tags[0] if tags else None
    rng = "%s..HEAD" % base if base else "HEAD"
    raw = git(root, "log", "--no-merges", "--format=%H%x1f%s%x1f%b%x1e", rng)
    out = []
    for rec in raw.split("\x1e"):
        rec = rec.strip("\n")
        if not rec:
            continue
        sha, subject, body = (rec.split("\x1f") + ["", ""])[:3]
        if subject.startswith("chore(release)"):
            continue
        out.append({"sha": sha, "subject": subject, "body": body})
    return base, out


def changed_runtime(root, sha):
    files = git(root, "show", "--name-only", "--format=", sha).split()
    return any(f.startswith(RUNTIME) or f in RUNTIME for f in files)


def decide(root, commits, major):
    level, why = "none", []
    for c in commits:
        m = CONV.match(c["subject"])
        lv = "none"
        if m:
            t = m.group("type").lower()
            if m.group("bang") or "BREAKING CHANGE" in c["body"]:
                lv = "minor" if major == 0 else "major"
            elif t == "feat":
                lv = "minor"
            elif t in ("fix", "perf"):
                lv = "patch"
        elif changed_runtime(root, c["sha"]):
            lv = "patch"
        if lv != "none":
            why.append("%s: %s" % (lv, c["subject"]))
        if RANK[lv] > RANK[level]:
            level = lv
    return level, why


def bump(version, level):
    ma, mi, pa = map(int, SEMVER.match(version).groups())
    if level == "major":
        return "%d.0.0" % (ma + 1)
    if level == "minor":
        return "%d.%d.0" % (ma, mi + 1)
    return "%d.%d.%d" % (ma, mi, pa + 1)


def replace_in(path, old, new, pattern):
    text = open(path, encoding="utf-8").read()
    out, n = re.subn(pattern % re.escape(old), lambda m: m.group(0).replace(old, new), text)
    if n:
        open(path, "w", encoding="utf-8").write(out)
    return n


def write_versions(root, old, new):
    done = []
    for rel in (".claude-plugin/plugin.json", ".claude-plugin/marketplace.json"):
        p = os.path.join(root, rel)
        if os.path.isfile(p):
            n = replace_in(p, old, new, r'"version"\s*:\s*"%s"')
            if n:
                done.append("%s (%d)" % (rel, n))
    for p in glob.glob(os.path.join(root, "lib", "*", "__init__.py")):
        n = replace_in(p, old, new, r'__version__\s*=\s*"%s"')
        if n:
            done.append("%s (%d)" % (os.path.relpath(p, root), n))
    return done


def changelog(root, new, commits):
    p = os.path.join(root, "CHANGELOG.md")
    if not os.path.isfile(p):
        return None, ""
    text = open(p, encoding="utf-8").read()
    today = datetime.date.today().isoformat()
    head = "## %s - %s" % (new, today)
    m = re.search(r"^## Unreleased\s*$", text, re.M)
    if m:
        text = text[:m.start()] + head + text[m.end():]
    else:
        lines = ["- %s (%s)" % (c["subject"], c["sha"][:7]) for c in commits]
        section = head + "\n\n" + "\n".join(lines) + "\n\n"
        i = text.find("\n## ")
        text = (text[:i + 1] + section + text[i + 1:]) if i >= 0 else text.rstrip("\n") + "\n\n" + section
    open(p, "w", encoding="utf-8").write(text)
    a = text.index(head)
    b = text.find("\n## ", a + 3)
    return p, text[a:b if b > 0 else len(text)].split("\n", 1)[1].strip() + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=".")
    ap.add_argument("--level", default="auto", choices=["auto", "patch", "minor", "major"])
    ap.add_argument("--apply", action="store_true", help="write the files (default: only say what would happen)")
    ap.add_argument("--notes-out", help="write the release notes (the changelog section) here")
    ap.add_argument("--github-output", action="store_true", help="append released/version/tag to $GITHUB_OUTPUT")
    a = ap.parse_args()
    root = os.path.abspath(a.root)
    old = current_version(root)
    if not SEMVER.match(old):
        raise SystemExit("release.py: version %r is not x.y.z" % old)
    base, commits = commits_since(root)
    level, why = decide(root, commits, int(old.split(".")[0]))
    if a.level != "auto":
        level, why = a.level, ["forced: --level %s" % a.level]
    result = {"current": old, "since": base, "commits": len(commits), "level": level, "reasons": why, "release": level != "none"}
    if level != "none":
        new = bump(old, level)
        result.update(version=new, tag="v" + new)
        if a.apply:
            result["written"] = write_versions(root, old, new)
            cl, notes = changelog(root, new, commits)
            if cl:
                result["written"].append("CHANGELOG.md")
            if a.notes_out:
                open(a.notes_out, "w", encoding="utf-8").write(notes or "\n".join("- " + c["subject"] for c in commits) + "\n")
    if a.github_output and os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write("released=%s\nversion=%s\ntag=%s\n" % (str(result["release"] and a.apply).lower(), result.get("version", ""), result.get("tag", "")))
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
