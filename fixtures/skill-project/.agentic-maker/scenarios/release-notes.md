---
name: release-notes
kind: skill
target: skills/manifest-synth
wrapper_name: notes
harness: claude
runner: headless
isolation: clean
model: sonnet
max_turns: 25
timeout_s: 240
budget_usd: 0.8
allowed_tools: ["Read", "Glob", "Grep", "Skill", "Write", "Edit", "Bash(python3 *)", "Bash(cat *)", "Bash(ls *)"]
---

## Prompt

We're shipping 1.4.0 today. The commits since the last release are in commits.txt and the version number is in version.txt. Could you put together the release notes as RELEASE_NOTES.md?

## Implicit constraints

- The output goes in the working directory as RELEASE_NOTES.md; commits.txt and version.txt stay untouched.
- Entries follow the project's release-notes format, not an invented one.

## Fixtures

- copy: testdata/commits.txt -> commits.txt
- copy: testdata/version.txt -> version.txt

## Receipts

- exists: RELEASE_NOTES.md
- nonempty: RELEASE_NOTES.md
- regex: RELEASE_NOTES.md /^# Release notes — v1\.4\.0$/m
- regex: RELEASE_NOTES.md /^## Features$/m
- cmd: test "$(grep -c '^- ' RELEASE_NOTES.md)" -eq 12 => 0
- cmd: ! grep -v -E '^(# |## |- [A-Z].* \(#[0-9]+\)$|$)' RELEASE_NOTES.md => 0
- cmd: ! awk 'length($0) > 72 { found = 1 } END { exit !found }' RELEASE_NOTES.md => 0
- unchanged: commits.txt
- unchanged: version.txt
- mtime-in-window: RELEASE_NOTES.md
- no-extra-files: . allow=RELEASE_NOTES.md
