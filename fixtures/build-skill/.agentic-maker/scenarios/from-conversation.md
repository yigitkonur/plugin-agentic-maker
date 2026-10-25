---
name: from-conversation
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

/agentic-maker:build-skill we just worked out how to deploy staging; the log of that session is in notes/session.md. Turn it into a skill for next time and put it in skills/deploy-staging/.

## Implicit constraints

- The corrections from the session (region, order of steps, token lifetime, the final health check) are what the skill is for, and they are in it exactly.
- Exactly one new skill is created.
- The log stays as it is.

## Fixtures

- copy: testdata/session/session.md -> notes/session.md

## Receipts

- exists: skills/deploy-staging/SKILL.md
- regex: skills/deploy-staging/SKILL.md /^name: deploy-staging$/m
- cmd: grep -rq -e '--region ams' skills/deploy-staging => 0
- cmd: grep -rq -e '--ttl 300' skills/deploy-staging => 0
- cmd: test "$(grep -n 'cache warm' skills/deploy-staging/SKILL.md | head -1 | cut -d: -f1)" -lt "$(grep -n 'db migrate' skills/deploy-staging/SKILL.md | head -1 | cut -d: -f1)" => 0
- cmd: grep -rq 'stagectl status --json' skills/deploy-staging => 0
- cmd: grep -rq 'healthy' skills/deploy-staging => 0
- cmd: test "$(ls -d skills/*/ | wc -l)" -eq 1 => 0
- cmd: ! grep -E '^description:.*[<>]' skills/deploy-staging/SKILL.md => 0
- cmd: test "$(wc -l < skills/deploy-staging/SKILL.md)" -lt 500 => 0
- unchanged: notes/session.md
