#!/usr/bin/env python3
"""Group conventional-commit lines into Features / Fixes / Other. Prints JSON."""
import json
import re
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "commits.txt"
groups = {"Features": [], "Fixes": [], "Other": []}
for line in open(path, encoding="utf-8"):
    m = re.match(r"^(\w+): (.+?) \(#(\d+)\)\s*$", line)
    if not m:
        continue
    kind, subject, pr = m.groups()
    key = {"feat": "Features", "fix": "Fixes"}.get(kind, "Other")
    groups[key].append({"subject": subject, "pr": int(pr)})
print(json.dumps({"groups": groups}, indent=2))
