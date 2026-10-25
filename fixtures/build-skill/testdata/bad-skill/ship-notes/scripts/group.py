#!/usr/bin/env python3
"""Group commit lines ('feat: x (#1)', 'fix: y (#2)') by type. Usage: group.py commits.txt"""
import sys, collections
groups = collections.defaultdict(list)
for line in open(sys.argv[1]):
    kind, _, rest = line.strip().partition(": ")
    groups[kind].append(rest)
for kind, items in sorted(groups.items()):
    print("## " + kind)
    for i in items:
        print("- " + i)
