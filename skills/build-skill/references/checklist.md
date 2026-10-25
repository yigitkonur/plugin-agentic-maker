# Ship checklist for a skill

> Read when: you think a skill is finished and need to confirm it before handing it over or installing it for others.

Set `S` to the skill directory (the folder holding `SKILL.md`), then run each line. A line passes when its command prints what is stated. Fix the first failing phase before moving on: later phases assume earlier ones.

```
S=path/to/skill
```

## 1. Frontmatter

- [ ] The file is named exactly `SKILL.md` (case-sensitive): `ls $S`.
- [ ] `head -1 $S/SKILL.md` prints `---`. Claude Code reads frontmatter only when `---` is line 1; a blank line above it loads the whole file as body text with no fields.
- [ ] A closing `---` exists: `grep -c '^---$' $S/SKILL.md` prints 2 or more.
- [ ] No tabs and no unquoted `: ` inside a value (invalid YAML loads the skill with empty metadata, so it never matches a request): `sed -n '2,/^---$/p' $S/SKILL.md | grep -nP '\t|^[a-z_-]+:.*: '` prints nothing.
- [ ] Field names are spelled exactly: `sed -n '2,/^---$/p' $S/SKILL.md | grep -o '^[a-z_-]*:'`. Claude Code ignores an unknown field without an error, so `discription:` fails silently. Common fields: `name`, `description`, `when_to_use`, `argument-hint`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `model`, `context`, `agent`, `hooks`, `paths`.
- [ ] `name` equals the directory name: `sed -n 's/^name: *//p' $S/SKILL.md` prints `basename $S`. The open skill spec asks for lowercase letters, digits and single hyphens, at most 64 characters, no leading or trailing hyphen, no "claude" or "anthropic"; Claude Code does not enforce these, so check them yourself. Claude Code refuses a `name` with `<`, `>` or control characters.
- [ ] No `<` or `>` in `name` or `description` (the open spec forbids them; `argument-hint` may use them): `grep -E '^(name|description):' $S/SKILL.md | grep -c '[<>]'` prints 0.
- [ ] A skill the user starts by hand (`/name`) has `disable-model-invocation: true`; the agent then cannot invoke it and its description is not loaded. A skill the agent should pick alone does not.
- [ ] `allowed-tools`, if present, lists only commands the skill runs: `grep '^allowed-tools:' $S/SKILL.md`.
- [ ] For a skill inside a plugin: `claude plugin validate <plugin-dir>` prints no `frontmatter:` warning for it.

## 2. Description

Rules and fixes are in `skills/agent-interface-design/references/skill/descriptions-that-trigger.md`; run only the measurable parts here.

- [ ] `sed -n 's/^description: //p' $S/SKILL.md | wc -c` prints 1025 or less (one-line descriptions only). Claude Code cuts `description` plus `when_to_use` at 1,536 characters in the skill listing, so put the key use case first.
- [ ] It says what the skill does (action and outcome) and when to use it, in words a user types, not the mechanism.
- [ ] It names the tools, formats or frameworks a user would say.
- [ ] One clause says what the skill is not for, if a neighbouring skill is easy to confuse with it.
- [ ] No event the agent cannot know ("when the build fails") unless the skill is meant to react to it.

## 3. Size

- [ ] `wc -l < $S/SKILL.md` prints 500 or less.
- [ ] Each reference covers one topic, with a `# Title` that names it; `find $S/references -name '*.md' -exec wc -l {} +` shows no file over 400 lines.
- [ ] More than 6 references: group them in subdirectories, at most `references/<group>/<file>.md`. No `README.md` in `references/`; no version suffix in a file name.
- [ ] Rules that every run needs sit at the top of `SKILL.md`, not in the middle; after compaction Claude Code keeps only the start of an invoked skill.

## 4. References routed

- [ ] No orphans: `find $S/references -name '*.md' | while read f; do grep -q "$(basename $f)" $S/SKILL.md || echo "orphan $f"; done` prints nothing.
- [ ] No dead pointers: `grep -o 'references/[A-Za-z0-9._/-]*\.md' $S/SKILL.md | sort -u | while read p; do test -f "$S/$p" || echo "missing $p"; done` prints nothing.
- [ ] Each routing row says when to read the file ("read X when Y"), not only that it exists.
- [ ] Each reference opens with a title and a one-line read-when: `head -3 $S/references/<file>.md`.

## 5. Scripts tested

Skip this phase when `$S/scripts` does not exist.

- [ ] Executable with a shebang: `ls -l $S/scripts` shows `x`; `head -1 $S/scripts/<file>` starts with `#!`.
- [ ] `SKILL.md` calls each script by `${CLAUDE_SKILL_DIR}/scripts/<file>`, not by a path relative to the working directory: `grep -n 'scripts/' $S/SKILL.md`.
- [ ] Each script ran once on real input from a different working directory (`cd /tmp` first); you saw the output and the exit code.
- [ ] Each script ran once on bad input and printed a message that says what to fix, with a non-zero exit.
- [ ] Every injected command in the skill (a backtick command after `!`) only reads and ends in `|| true`: a non-zero exit aborts the whole invocation (`Shell command failed for pattern`) and the agent never sees the skill. Exit code 1 from a search or compare command is the one exception.
- [ ] No personal path, email or token: `grep -rnE '/Us[e]rs/|@gma[i]l\.|ghp_|sk-[A-Za-z0-9]{20}' $S` prints nothing.

## 6. Fresh-agent run

The author's own reading proves nothing: the author already knows what the text means.

- [ ] Write one everyday request that does not name the skill. Run it in a fresh session with the skill loaded:
  `claude -p "<request>" --plugin-dir <plugin-dir> --output-format stream-json --verbose | grep -c '"name":"Skill"'` prints 1 or more. A 0 usually means the description failed (phase 2).
- [ ] Run it 3 times, plus 3 paraphrases. The skill is chosen every time.
- [ ] Run 3 requests the skill is not for. The same command prints 0 for each.
- [ ] Read one whole execution, not only the final answer. Note every tool call that was a guess, a retry or a wrong path; each is a text defect to fix.
- [ ] The output has the format `SKILL.md` states, with no step skipped.
- [ ] Run once more with your other skills installed; a neighbour that wins is a description defect.

How to write the text so a fresh agent follows it: `skills/agent-interface-design/references/skill/text-as-program.md`.

## 7. Last step

- [ ] Run `/agentic-maker:derail <skill-dir>` on the skill. It runs fresh agents, reads their executions, and fixes the text that misled them. Ship when a run ends with no finding left to fix.
