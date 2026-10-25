---
name: shipnotes
description: Helps with <release> stuff.
---

# Ship notes

Turn the commit list into release notes.

1. Group the commits: run `python3 scripts/group.py commits.txt`.
2. Write the notes in the format described in [formats](references/format.md).
3. Never write an entry longer than 72 characters. Never use the passive voice. Never invent a PR number.
4. Save the result as RELEASE_NOTES.md.
