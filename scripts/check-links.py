#!/usr/bin/env python3
"""Relative markdown links must resolve. Usage: check-links.py [root]. Exit 1 when any are broken. Python 3.9+."""
import os
import re
import sys

LINK = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})")


def main(argv):
    root = os.path.abspath(argv[0] if argv else os.path.join(os.path.dirname(__file__), ".."))
    broken, total = [], 0
    for base in ("skills", "agents", "docs", "README.md"):
        p0 = os.path.join(root, base)
        paths = [p0] if os.path.isfile(p0) else [os.path.join(dp, f) for dp, _, fs in os.walk(p0) for f in fs if f.endswith(".md")]
        for p in paths:
            fence = None
            for n, line in enumerate(open(p, encoding="utf-8", errors="replace"), 1):
                m = FENCE.match(line)
                if m:
                    fence = None if (fence and line.strip().startswith(fence)) else (fence or m.group(1))
                    continue
                if fence:
                    continue
                for t in LINK.findall(re.sub(r"`[^`]*`", "", line)):
                    if re.match(r"^[a-z]+:", t) or t.startswith("#") or t.startswith("<"):
                        continue
                    target = t.split("#", 1)[0]
                    total += 1
                    if target and not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(p), target))):
                        broken.append("%s:%d -> %s" % (os.path.relpath(p, root), n, t))
    for b in broken[:60]:
        print("broken link:", b)
    print("check-links: %d links, %d broken" % (total, len(broken)))
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
