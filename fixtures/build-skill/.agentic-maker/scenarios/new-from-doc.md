---
name: new-from-doc
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

/agentic-maker:build-skill a skill that teaches coding agents how to use our internal acme-report CLI. Everything you need to know about the CLI is in docs/acme-report.md; there is no internet. Put the skill in skills/acme-report/.

## Implicit constraints

- The new skill lives in skills/acme-report/ with a SKILL.md.
- Every fact in it comes from docs/acme-report.md; that file stays untouched.
- It is checked before it is called done (frontmatter, size, links).

## Fixtures

- copy: testdata/acme-report.md -> docs/acme-report.md

## Receipts

- exists: skills/acme-report/SKILL.md
- regex: skills/acme-report/SKILL.md /^name: acme-report$/m
- regex: skills/acme-report/SKILL.md /^description: .{20,}/m
- cmd: test "$(wc -l < skills/acme-report/SKILL.md)" -lt 500 => 0
- cmd: ! grep -E '^description:.*[<>]' skills/acme-report/SKILL.md => 0
- cmd: test "$(sed -n 's/^description: //p' skills/acme-report/SKILL.md | head -1 | wc -c)" -lt 1025 => 0
- cmd: grep -rqi 'ACME_TOKEN' skills/acme-report => 0
- cmd: grep -rq -e '--force' skills/acme-report => 0
- cmd: grep -rqE '400' skills/acme-report => 0
- cmd: ! grep -rqiE 'TODO|lorem|FIXME' skills/acme-report => 0
- cmd: cd skills/acme-report && for f in $(grep -o 'references/[A-Za-z0-9_./-]*\.md' SKILL.md | sort -u); do test -f "$f" || exit 1; done => 0
- unchanged: docs/acme-report.md
