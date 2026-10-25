# Content anti-patterns in skills

> Read when: you review a skill's text before shipping it, or a run shows an agent skipping a step, guessing, loading the wrong file or never choosing the skill.

Each entry: the mistake, how to recognise it, the fix. Descriptions and body wording are covered in depth by `skills/agent-interface-design/references/skill/descriptions-that-trigger.md` and `skills/agent-interface-design/references/skill/text-as-program.md`; this page only lists the traps.

## Skill is not chosen, or chosen wrongly

| Mistake | Recognise it | Fix |
|---|---|---|
| Vague description | "Helps with code reviews." No verb, no situation, no words a user types | Lead with the job in user words: what the user has, what they want, what the skill produces. Put the key use first: description plus `when_to_use` is cut at 1,536 characters in the listing |
| No exclusion on a broad skill | Topic like "data analysis" and nothing about neighbours | Add one clause: "Not for X (use Y)" |
| No frontmatter delimiters | File starts with `name:` or a blank line, no `---` on line 1 | Put `---` on line 1, close it before the first heading; the skill otherwise loads without metadata |
| `<` or `>` in `name`, or a reserved name | Claude Code refuses a `name` containing `<` or `>`; `anthropic-skills` (and names inside that namespace) and a folder named `synced` are reserved | Use a plain descriptive name without those characters or words |

## Skill makes the agent do unsafe or unrequested things

| Mistake | Recognise it | Fix |
|---|---|---|
| Over-broad `allowed-tools` | Lists `Bash`, `Write`, `Edit` on a skill that only reads | List only the tools the steps use, e.g. `allowed-tools: Read Grep Glob` (Claude Code takes a space- or comma-separated string, or a YAML list). The grant lasts only for the turn that invokes the skill |
| Side effects with no gate | Deploy, delete, send, publish steps that run as soon as the skill is chosen | Set `disable-model-invocation: true` so only `/name` starts it, and add a first step that asks the user to confirm the target and exact command before anything irreversible |
| Deterministic check written as prose | "Make sure the output has all required sections" | Bundle a script and name the command and expected result: `python3 ${CLAUDE_SKILL_DIR}/scripts/check.py out.md` prints `0 problems`. Prose checks get skimmed |

## Body text makes the agent guess

| Mistake | Recognise it | Fix |
|---|---|---|
| Rule overload | A long "always/never" list (dozens of lines), many unrelated to the task | Keep 5 to 7 rules that change the outcome; move edge cases to a reference opened on a named condition |
| No example output | Steps say "create the component" but never show one | Include at least one complete input and output pair |
| Adjectives instead of numbers | "keep it short", "proper formatting", "a few" | Replace each with a count, a limit or a pattern |
| Steps without evidence | A phase the agent can finish without running or reading anything | End each phase with a command and its expected result |
| Stale API or flag names | Examples use removed flags, old versions, no version noted | Run each command in the skill once; state the version it was run against; delete what fails |
| Wrong or relative paths | `scripts/run.py` with no base; `reference/` for `references/` | Use `${CLAUDE_SKILL_DIR}` or "relative to this skill's directory"; check every path against `ls` |

## Structure hides content or wastes context

| Mistake | Recognise it | Fix |
|---|---|---|
| SKILL.md over 500 lines | `wc -l SKILL.md` above 500 | Keep routing, the main workflow and the 80% case in SKILL.md; move the rest to `references/` |
| SKILL.md that only says "see references/" | No workflow, no decision, no quick start | SKILL.md must be enough to finish the common task alone, plus a "read X when Y" table |
| Orphaned reference | A file in `references/` that no line in SKILL.md names (old drafts, notes, backups) | Link it from a "read X when Y" row or delete it |
| Mixed-topic reference | `everything.md` covering auth, deploys and errors | One decision or topic per file, each opened with a `> Read when:` line |
| Deep nesting | `references/<a>/<b>/<c>/<file>.md` | Keep to `references/<topic>/file.md` at most; split the skill if more depth seems needed |

## Skill is never tested

| Mistake | Recognise it | Fix |
|---|---|---|
| Shipped on a read-through | No fresh-agent run exists | Run `/agentic-maker:derail <skill-dir>` on an everyday request that does not name the skill; read the execution; fix the text that misled the agent. Also run 5 should-trigger queries, 5 should-not-trigger queries and 1 full workflow |
| No success criterion | "Should work well" | Before building, write: the request, the output expected, a trigger rate to reach, a tool-call budget and a token budget |
| Static checks skipped | Structure errors found only at run time | Run `/agentic-maker:audit <skill-dir>` (read-only probes) before the derail run |
