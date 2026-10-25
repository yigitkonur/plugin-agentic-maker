# How strict to write each instruction

> Read when: you draft or revise the steps of a skill and must decide, step by step, whether to give an exact command, a fixed shape, or a goal; or a run shows the agent skipping a step, improvising where it should not, or following a rule rigidly where judgment was needed.

Strictness is chosen per step, not per skill. Ask one question of each step: what happens if the agent does it differently?

## The three levels

| If a deviation... | Level | You write |
|---|---|---|
| gives an equally good result | Goal | The outcome and the constraint. No method. |
| degrades the result (step skipped, wrong order, missing part) | Shape | Ordered steps or required fields. Content is the agent's. |
| breaks the result (wrong flag, path, string) | Literal | The exact command, path or text. Prefer a script. |

If you cannot predict the deviation, test it: copy the skill, delete that instruction from the copy, run fresh agents on the copy with `/agentic-maker:derail <copy-dir>`, and read what they do.

## Decision table

| Step type | Level | Wording example |
|---|---|---|
| Pick an approach where the agent's defaults are good (language, framework, file format) | Goal | "Inventory the workspace enough to know what already exists before you draft." |
| Workflow order that matters but content varies | Shape | "Before synthesizing, build a table with columns Source, Strengths, Gaps, Decision. Every row ends with a decision." |
| Exact command, flag or path | Literal | "Run `python3 ${CLAUDE_SKILL_DIR}/scripts/check.py <dir>`. Expect `0 violations`." |
| Verification right after a change | Literal plus timing | "Immediately after the edit, run the test. Do not continue until it fails for the stated reason." |
| Destructive or irreversible action (delete, overwrite, push) | Literal plus gate | "Back up first. Never delete a file you have not listed to the user." |
| Rule that must hold every time (safety, discipline) | Firm rule | "Write the test before the code. If code came first, delete it and start over." |
| Step agents tend to skip | Shape plus announcement | "Before step 1, state: 'Using <skill-name>'." |
| Collaboration, review, tone | Goal, shared voice | "Give your honest technical judgment, including when it disagrees with mine." |
| Reference or format facts (syntax, field names) | Literal, no persuasion | State the facts. Add no emphasis. |

## When firm wording helps

Use firm wording on the few steps where a miss is costly, and only there.

- **Plain imperative, no hedge.** "Run the test before merging." beats "Consider running the test when feasible." A hedge turns a rule into an option.
- **Close the exception.** Say "No exceptions" only if there are none. Otherwise state the exception explicitly.
- **Say when.** "Immediately after", "before the next step" stop the agent from deferring a check. A check with no timing gets deferred.
- **Announce.** Make the agent write one line saying it is following the skill, before the first step. A later skip then contradicts its own statement. Use it for long multi-step flows, not one-shot tasks.
- **State the failure.** "Checklists without tracking get steps skipped." Say what goes wrong, in one sentence, next to the rule. Only claim what you have seen.
- **Give the reason.** One clause ("the parser rejects tabs in this file") helps the agent handle cases the rule did not list.

## When firm wording backfires

- **Everything firm.** If every line is a MUST, nothing marks the few that break something when skipped, and the agent loses room to adapt where adapting helps. Cap firm rules at the few that break something when skipped.
- **Firm rule on a judgment step.** The agent applies it rigidly to cases it was not written for. Give the goal and the reason instead.
- **Warm or pleading wording.** "If you have time, maybe consider..." and "feel free to ignore" read as optional. Warmth also pushes agents to agree with the user rather than report what is true.
- **Shared-team voice on a hard rule.** "We" makes a rule feel negotiable. Use the shared voice for collaboration steps and the imperative for rules; do not mix them in one step.
- **Invented authority or urgency.** Do not write "everyone agrees" or fake deadlines. Test: would the user endorse the technique if they saw it? Invented authority fails.
- **Stacking.** Two or three devices on one rule (imperative, timing, reason) are enough. More dilutes each.
- **Literal text that ages.** A pasted command goes stale when the tool changes. Move it into `scripts/` and call the script, so one fix reaches every step that uses it.

## Voice by level and skill type

- Goal steps pair with the shared voice ("we"); literal steps pair with the imperative, no hedge. A shape step is firm on the order and open on the content.
- Discipline skill (testing, verification): firm rules, announcement, stated failure. Guidance skill: moderate firmness plus shared voice. Collaborative skill: shared voice plus announcement. Reference skill: facts only.

## Move a step up or down

After a test run, change one step at a time:

| Observed | Change |
|---|---|
| Agent guesses wrong at a goal step | Goal to shape: add the fields or order |
| Agent gets a shape step subtly wrong | Shape to literal: give the exact value |
| Literal step keeps drifting or going stale | Literal to script: put the logic in `scripts/` |
| Shape step with columns or order that do not matter | Shape to goal: the structure is dead weight |
| Agent does the right thing without the instruction | Delete or loosen it |

Anti-patterns to remove on sight:

- Listing "read the file with the Read tool": the agent knows how.
- "Validate the skill" with no command: give the command and the expected output.
- One step that says "use your judgment" and then "run exactly this": pick one level for the step.
- Uniform literal text throughout (a manual) or uniform goals throughout (no definition of done).

## Related pages

- `skills/agent-interface-design/references/skill/text-as-program.md`: exact paths, numbers instead of adjectives, a check on every phase.
- `skills/agent-interface-design/references/skill/descriptions-that-trigger.md`: the description is the one place to write for matching, not for compliance.
- `/agentic-maker:derail <skill-dir>`: run fresh agents on the skill and fix the text that misled them. This is how you test a strictness choice.
