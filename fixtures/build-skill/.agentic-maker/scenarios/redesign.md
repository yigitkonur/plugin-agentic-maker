---
name: redesign
kind: plugin
target: ../..
leave_out: ["fixtures", "evals", "docs"]
runner: headless
isolation: clean
model: sonnet
max_turns: 40
timeout_s: 420
budget_usd: 1.5
allowed_tools: ["Read", "Glob", "Grep", "Write", "Edit", "Skill", "Bash(ls *)", "Bash(cat *)", "Bash(wc *)", "Bash(grep *)", "Bash(mkdir *)", "Bash(mv *)", "Bash(python3 *)", "Bash(claude plugin validate *)", "Bash(agentic-maker *)"]
---

## Prompt

/agentic-maker:build-skill redesign the skill in skills/ship-notes/ so that it is picked when someone asks for release notes or a changelog, and so that everything it points at actually works. Keep its references and script.

## Implicit constraints

- The skill keeps its directory, its reference page and its script; they are fixed or re-pointed, not deleted.
- Whatever the skill tells an agent to run must work from the project folder, not only from inside the skill folder.
- The rules are fixed at their cause, not patched with more rules.

## Fixtures

- copy: testdata/bad-skill/ship-notes -> skills/ship-notes

## Receipts

- exists: skills/ship-notes/SKILL.md
- regex: skills/ship-notes/SKILL.md /^name: ship-notes$/m
- cmd: ! grep -E '^description:.*[<>]' skills/ship-notes/SKILL.md => 0
- regex: skills/ship-notes/SKILL.md /^description: .*release notes/mi
- cmd: test "$(sed -n 's/^description: //p' skills/ship-notes/SKILL.md | head -1 | wc -c)" -lt 1025 => 0
- cmd: test "$(wc -l < skills/ship-notes/SKILL.md)" -lt 500 => 0
- cmd: cd skills/ship-notes && for f in $(grep -o 'references/[A-Za-z0-9_./-]*\.md' SKILL.md | sort -u); do test -f "$f" || exit 1; done => 0
- cmd: ! grep -q 'python3 scripts/group.py' skills/ship-notes/SKILL.md => 0
- cmd: grep -qE '(skills/ship-notes|\$\{CLAUDE_SKILL_DIR\})/scripts/group\.py' skills/ship-notes/SKILL.md => 0
- exists: skills/ship-notes/references/formats.md
- exists: skills/ship-notes/scripts/group.py
- cmd: test "$(grep -ciE '^[0-9]*\.? *never ' skills/ship-notes/SKILL.md)" -lt 3 => 0
- cmd: test "$(ls .agentic-maker/scenarios/*.md 2>/dev/null | wc -l)" -ge 3 => 0
