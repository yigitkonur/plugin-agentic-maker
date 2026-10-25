---
name: merge
kind: plugin
target: ../..
runner: headless
isolation: clean
model: sonnet
max_turns: 40
timeout_s: 420
budget_usd: 1.5
allowed_tools: ["Read", "Glob", "Grep", "Write", "Edit", "Skill", "Bash(ls *)", "Bash(cat *)", "Bash(wc *)", "Bash(grep *)", "Bash(mkdir *)", "Bash(mv *)", "Bash(python3 *)", "Bash(claude plugin validate *)"]
---

## Prompt

/agentic-maker:build-skill we have two small skills, skills/lint-js and skills/lint-py. Merge them into one skill called lint in skills/lint/ that covers both languages. Leave the two old ones as they are for now.

## Implicit constraints

- One new skill, `lint`, that an agent can use for a JavaScript repo, a Python repo or a mixed one.
- Both commands survive exactly; nothing is invented.
- The two source skills are untouched.

## Fixtures

- copy: testdata/merge/lint-js -> skills/lint-js
- copy: testdata/merge/lint-py -> skills/lint-py

## Receipts

- exists: skills/lint/SKILL.md
- regex: skills/lint/SKILL.md /^name: lint$/m
- cmd: grep -q 'npx eslint --max-warnings 0 \.' skills/lint/SKILL.md => 0
- cmd: grep -q 'ruff format --check \.' skills/lint/SKILL.md => 0
- regex: skills/lint/SKILL.md /^description: .*(javascript|typescript)/mi
- regex: skills/lint/SKILL.md /^description: .*python/mi
- cmd: ! grep -E '^description:.*[<>]' skills/lint/SKILL.md => 0
- cmd: test "$(wc -l < skills/lint/SKILL.md)" -lt 500 => 0
- unchanged: skills/lint-js/SKILL.md
- unchanged: skills/lint-py/SKILL.md
