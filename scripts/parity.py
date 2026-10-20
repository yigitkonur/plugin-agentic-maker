#!/usr/bin/env python3
"""Parity checker: does every heading of the three source skills have a destination?

Hard gate (exit 1): a source heading (H1-H3, outside code fences) that is neither
claimed by a provenance marker in the new corpus nor listed in docs/parity/dropped.tsv
with a reason, or a marker that names a heading that does not exist.

Soft reports (never fail): table first-column keys and backticked tokens / thresholds
from the sources that no longer appear anywhere in the new corpus.

Python 3.9+, standard library only.
"""
import argparse
import csv
import os
import re
import sys

SKILLS = ("audit-agentic-cli", "audit-agentic-mcp", "audit-skill-by-derailment")
MARKER_RE = re.compile(r"<!--\s*src:\s*(.*?)\s*-->", re.S)
HEADING_RE = re.compile(r"^(#{1,3})[ \t]+(.+?)[ \t]*#*[ \t]*$")
FENCE_RE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})")
TOKEN_RE = re.compile(r"`([^`\n]{3,60})`")
NUMBER_RE = re.compile(r"\b\d+(?:[.,]\d+)?\s?(?:KB|MB|ms|tokens?|chars?|seconds?|minutes?|hours?|%|x|×)\b", re.I)
IDENT_RE = re.compile(r"^[A-Za-z0-9_./:=<>$@{}\[\]*#~%|\\\-]+$")


def norm_heading(text):
    return re.sub(r"\s+", " ", text.strip())


def iter_lines_outside_fences(text):
    """Yield (lineno, line, in_fence) for every line."""
    fence = None
    for i, line in enumerate(text.splitlines(), 1):
        m = FENCE_RE.match(line)
        if m:
            tok = m.group(1)
            if fence is None:
                fence = (tok[0], len(tok))
                yield i, line, True
                continue
            if tok[0] == fence[0] and len(tok) >= fence[1] and line.strip() == tok:
                fence = None
                yield i, line, True
                continue
        yield i, line, fence is not None


def extract_headings(path):
    """Return [(key_suffix_text, level, lineno)] with ~n suffix for repeated texts."""
    seen = {}
    out = []
    with open(path, encoding="utf-8") as f:
        text = f.read()
    for i, line, infence in iter_lines_outside_fences(text):
        if infence:
            continue
        m = HEADING_RE.match(line)
        if not m:
            continue
        t = norm_heading(m.group(2))
        seen[t] = seen.get(t, 0) + 1
        key = t if seen[t] == 1 else "%s~%d" % (t, seen[t])
        out.append((key, len(m.group(1)), i))
    return out


def source_files(src):
    md, other = [], []
    for s in SKILLS:
        for root, _, files in os.walk(os.path.join(src, s)):
            for fn in sorted(files):
                p = os.path.join(root, fn)
                rel = os.path.relpath(p, src)
                (md if fn.endswith(".md") else other).append(rel)
    return sorted(md), sorted(other)


def dest_files(dest):
    out = []
    for base in ("skills", "agents", "docs/parity"):
        for root, _, files in os.walk(os.path.join(dest, base)):
            for fn in files:
                if fn.endswith(".md"):
                    out.append(os.path.join(root, fn))
    return sorted(out)


def read_tsv(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            rows.append(line.split("\t"))
    return rows


def collect_markers(dest):
    """Return {source_key: [destination_file:line, ...]}."""
    claims = {}
    for p in dest_files(dest):
        with open(p, encoding="utf-8") as f:
            text = f.read()
        rel = os.path.relpath(p, dest)
        if rel.startswith("docs/parity"):
            continue
        for m in MARKER_RE.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            for key in m.group(1).split("|"):
                key = key.strip()
                if key:
                    claims.setdefault(key, []).append("%s:%d" % (rel, line))
    return claims


def corpus_text(dest):
    chunks = []
    for p in dest_files(dest):
        rel = os.path.relpath(p, dest)
        if rel.startswith("docs/parity") or rel.startswith("docs/design"):
            continue
        with open(p, encoding="utf-8") as f:
            chunks.append(f.read())
    t = "\n".join(chunks).lower().replace("`", "")
    return re.sub(r"\s+", " ", t)


def table_keys(text):
    keys = []
    for i, line, infence in iter_lines_outside_fences(text):
        if infence or not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not cells or re.fullmatch(r"[:\- ]+", cells[0] or "-"):
            continue
        k = re.sub(r"[*`]", "", cells[0]).strip()
        if len(k) >= 2:
            keys.append(k)
    return keys[1:] if keys else []  # drop the header row


def tokens_of(text):
    toks = set()
    for i, line, infence in iter_lines_outside_fences(text):
        if infence:
            continue
        for m in TOKEN_RE.finditer(line):
            t = m.group(1).strip()
            if IDENT_RE.match(t) and not t.isdigit():
                toks.add(t)
        for m in NUMBER_RE.finditer(line):
            toks.add(m.group(0).strip())
    return toks


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("command", choices=["check"], help="check: write the ledger and enforce the heading gate")
    ap.add_argument("--src", default="/tmp/am-src/skills-by-yigitkonur/skills", help="directory holding the three source skills")
    ap.add_argument("--dest", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))), help="repo root")
    ap.add_argument("--soft", action="store_true", help="also write table-key and token survival reports")
    ap.add_argument("--no-write", action="store_true", help="do not write docs/parity/*.tsv")
    args = ap.parse_args(argv)

    if not os.path.isdir(args.src):
        sys.stderr.write("source directory not found: %s\n" % args.src)
        return 2
    md, other = source_files(args.src)
    parity_dir = os.path.join(args.dest, "docs", "parity")
    dropped = {r[0]: (r[1] if len(r) > 1 else "") for r in read_tsv(os.path.join(parity_dir, "dropped.tsv"))}
    scripts = {r[0]: r for r in read_tsv(os.path.join(parity_dir, "files.tsv"))}
    claims = collect_markers(args.dest)
    # headings the author clearly intended but a stray code fence in the source hides from a strict parse
    extra = {}
    for r in read_tsv(os.path.join(parity_dir, "extra-headings.tsv")):
        if len(r) >= 4:
            extra.setdefault(r[0], []).append((norm_heading(r[3]), int(r[2]), int(r[1])))

    ledger, all_keys = [], set()
    unmapped, bad_reasons = [], []
    for rel in md:
        found = extract_headings(os.path.join(args.src, rel))
        have = {k for k, _, _ in found}
        found += [(k, lv, ln) for k, lv, ln in extra.get(rel, []) if k not in have]
        for key, level, line in sorted(found, key=lambda r: r[2]):
            full = "%s#%s" % (rel, key)
            all_keys.add(full)
            if full in claims:
                ledger.append((full, level, line, "mapped", ";".join(claims[full]), ""))
            elif full in dropped:
                if len(dropped[full].strip()) < 10:
                    bad_reasons.append(full)
                ledger.append((full, level, line, "dropped", "", dropped[full]))
            else:
                unmapped.append(full)
                ledger.append((full, level, line, "UNMAPPED", "", ""))
    dangling = sorted(k for k in claims if k not in all_keys)
    dangling_dropped = sorted(k for k in dropped if k not in all_keys)
    unlisted_files = sorted(f for f in other if f not in scripts)

    if not args.no_write:
        os.makedirs(parity_dir, exist_ok=True)
        with open(os.path.join(parity_dir, "ledger.tsv"), "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter="\t", lineterminator="\n")
            w.writerow(["source_heading", "level", "line", "status", "destination", "reason"])
            w.writerows(ledger)

    n = len(ledger)
    mapped = sum(1 for r in ledger if r[3] == "mapped")
    drop = sum(1 for r in ledger if r[3] == "dropped")
    print("source headings: %d | mapped: %d | dropped: %d | UNMAPPED: %d | dangling markers: %d | dangling drops: %d | non-md files without a row in files.tsv: %d"
          % (n, mapped, drop, len(unmapped), len(dangling), len(dangling_dropped), len(unlisted_files)))
    for k in dangling[:20]:
        print("  dangling marker: %s  (%s)" % (k, ", ".join(claims[k][:2])))
    for k in bad_reasons[:20]:
        print("  dropped without a real reason: %s" % k)
    for k in unlisted_files[:20]:
        print("  file without a row: %s" % k)

    if args.soft:
        corpus = corpus_text(args.dest)
        miss_keys, miss_tokens = [], []
        for rel in md:
            with open(os.path.join(args.src, rel), encoding="utf-8") as f:
                text = f.read()
            for k in table_keys(text):
                if re.sub(r"\s+", " ", k.lower()) not in corpus:
                    miss_keys.append((rel, k))
            for t in sorted(tokens_of(text)):
                if t.lower() not in corpus:
                    miss_tokens.append((rel, t))
        if not args.no_write:
            for name, rows in (("table-keys-missing.tsv", miss_keys), ("tokens-missing.tsv", miss_tokens)):
                with open(os.path.join(parity_dir, name), "w", encoding="utf-8", newline="") as f:
                    w = csv.writer(f, delimiter="\t", lineterminator="\n")
                    w.writerow(["source_file", "item"])
                    w.writerows(rows)
        print("soft: table keys not found in the new corpus: %d | tokens/thresholds not found: %d" % (len(miss_keys), len(miss_tokens)))

    bad = len(unmapped) + len(dangling) + len(bad_reasons) + len(dangling_dropped) + len(unlisted_files)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
