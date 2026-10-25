# A skill does not trigger, load or behave

> Read when: a skill you built is missing from the skill list, is never chosen, is chosen but not followed, fires on the wrong request, fails in a script, or leaves a reference unread.

Find the row that matches what you see, run its check, change the one piece of text it names. Change one thing per run.

## Symptom, cause, check, fix

| Symptom | Likely cause | Check | Fix |
|---|---|---|---|
| 1. Not listed | Bad path, bad frontmatter, or a directory created after the session started | Ask "What skills are available?" and run `/skills`. Run `claude plugin validate <skills-dir>` (v2.1.233+). Run `claude --debug` for the parse error. | See 1 below. |
| 2. Listed, never chosen | Description lacks the words the user types, or was cut from the listing | Run the request 5 times without naming the skill. Count how often it is chosen (goal: 90%+ of relevant requests, 0% of unrelated). Run `/doctor` for listing cost. | See 2 below. |
| 3. Chosen, then ignored | Steps vague, key rule buried, or context compacted | Read the transcript. Find the first step the agent skipped or guessed. | See 3 below. |
| 4. Over-triggering | Description too broad, or a neighbour overlaps | Run 10 unrelated requests. More than 1 hit means too broad. | See 4 below. |
| 5. Script fails | Wrong path, missing interpreter, failed injected command | Run the exact command from the skill text in the session's working directory. | See 5 below. |
| 6. Reference never read | No routing line points to it, or the line does not say when | `grep -n "<file>" SKILL.md`. Read the transcript for any Read of the file. | See 6 below. |

### 1. Not listed

- Frontmatter that does not parse does not hide the skill: the body loads with empty metadata, `/skill-name` still works, and the agent cannot match the `description`. Fix the YAML (`---` on line 1, closing `---`, quote values containing a colon, spaces not tabs).
- A skills directory created after the session began is not watched. Run `/reload-skills`. Edits in a watched directory apply live.
- A `.claude/skills/` below the directory where Claude started loads only after the agent reads or edits a file under it. Start Claude in that directory or run `/add-dir <path>` (v2.1.257+).
- `user-invocable: false` hides the skill from the `/` menu; the agent can still choose it.
- If `/skill-name` is also unknown, the name was refused (control characters, `<`, `>`, odd spaces). Use lowercase letters, digits and hyphens.

### 2. Listed but never chosen

- The listing shows name, `description` and `when_to_use`. Rewrite the description in the words of the request and lead with the job and key use case. Rules: `skills/agent-interface-design/references/skill/descriptions-that-trigger.md`.
- `description` plus `when_to_use` is cut at 1,536 characters. With many skills, the listing also drops descriptions to fit a budget of 1% of the context window, least-used first. Run `/doctor`. Raise `skillListingBudgetFraction` (for example `0.02`) or `SLASH_COMMAND_TOOL_CHAR_BUDGET`, or turn off unused skills.
- `disable-model-invocation: true` means the agent never chooses it. Remove it if the agent should.
- `paths` limits automatic loading to files matching the globs, relative to the current directory. Files outside it never match.
- Do not ask the agent "when would you use this skill?"; it quotes the description back. Measure real choices.

### 3. Chosen but ignored

- A vague step gets guessed. Replace the adjective with a number or a command. A rule the agent must never skip belongs in a hook, not prose. Rules: `skills/agent-interface-design/references/skill/text-as-program.md`.
- Put the rule that matters most at the top of SKILL.md. After compaction Claude Code re-attaches only the first 5,000 tokens of each invoked skill, within 25,000 tokens for all skills; invoke the skill again to restore it.
- The skill text is read once, at invocation. Write guidance to cover the whole task ("run the tests after every edit"), not one moment.
- Keep SKILL.md below 500 lines and at most 7 rules. Move detail into references.

### 4. Over-triggering

- Add the situation it is not for, in one clause: "Not for X (use `other-skill`)". Add the same clause to the neighbour.
- Replace generic nouns ("data", "files", "project") with the specific object and format.
- If it should only run on request, set `disable-model-invocation: true`. Its description then costs no context.

### 5. Script fails

- Use `${CLAUDE_SKILL_DIR}/scripts/x.py`, not `scripts/x.py`. The working directory is the session's, not the skill folder.
- Invoke with the interpreter (`python3 ${CLAUDE_SKILL_DIR}/scripts/x.py`) so the file mode does not matter.
- Test prerequisites before step 1: `command -v python3 || echo MISSING`.
- A failing `` !`command` `` aborts the whole invocation: the agent never sees the skill. End each with `|| true`.
- A `Bash(...)` rule must match every part of a chained command, and commands built with shell variables prompt. Tell the agent to run one command per call with literal paths.

### 6. Reference never read

- SKILL.md needs one row per file: "Read `references/<file>.md` when <situation>". Use the exact path.
- The page's own `> Read when:` line must name the same situation, since that is what the agent matches.
- Keep one decision per reference.

## Read signals from real use

Each signal points to the text that caused it.

| Signal in real use | Text to change |
|---|---|
| User types `/skill-name` by hand | `description`: add the user's words |
| User re-explains the workflow each time | `description`: the skill is not being chosen |
| Agent picks a different skill | `description` of both: state what each does that the other does not |
| User turns the skill off | `description`: too broad (section 4) |
| User corrects the agent mid-run | The step before the correction: make it exact |
| Output format varies between runs | Add one format block and one full example |
| Same step skipped across runs | Move it up, add a check command, or add a hook |
| Tool or script errors | Path, tool name or prerequisite check |

Procedure:

1. Collect 5 or more transcripts of real use, including the ones where the user corrected the agent.
2. For each signal, find the first line of the transcript where the agent deviated. Quote the skill sentence it read there.
3. Edit that sentence. Do not add a new rule next to a bad one.
4. Re-run the same request 3 times. Keep the edit only if the signal goes away.
5. Fix in this order: choice (`description`), then steps (SKILL.md body), then edge cases (references).

Without waiting for users, use `/agentic-maker:derail <skill-dir>`. It runs the skill, reads the execution and names the text that misled. `/agentic-maker:audit` probes a skill directory read-only, and `agentic-maker scan skill <path>` locates skills. To measure choice rate in CI, write a `claude plugin eval` case with a `tool_used: Skill` grader.
