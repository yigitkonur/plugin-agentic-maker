# Process anti-patterns when authoring a skill

> Read when: you are about to build or revise a skill and want to avoid the common process mistakes, or a review of how a skill was built shows skipped steps, missing evidence or a flat tone.

These are mistakes in how the skill is built, not in the finished text. For the finished text (descriptions, body) see `skills/agent-interface-design/references/skill/descriptions-that-trigger.md` and `skills/agent-interface-design/references/skill/text-as-program.md`. Each item gives the mistake, the corrective step, and a check you can run on your own work.

## Context and pacing

**AP-25 Reference overload.** Mistake: opening every reference file before drafting. Result: context fills, you lose track of which file drove which decision, and the output blends sources without attribution.
- Fix: open 3 to 5 files for the current step, picked from the routing table of the build workflow you follow. Close the step, then open the next set.
- Check: more than 5 reference files read before the draft exists means stop and pick.

**AP-26 Output batching.** Mistake: holding every artifact (outline, description, draft, test results) until the end. Result: errors survive because nobody reviewed the intermediate state.
- Fix: show each artifact right after the step that produces it, then continue.
- Check: you reached the last step and have shown nothing yet.

**AP-31 Checklist as workflow.** Mistake: working through every item of a 100-item checklist for every task. Result: a one-line revision costs as much as a new build, and late items get rubber-stamped.
- Fix: split the list by phase. Mark each item "draft essential" or "final audit only". Run the draft-essential items (early phases) on every task. Run the final-audit items only for a full quality pass, and only after a complete draft exists.
- Check: you are running audit items with no complete draft.

## Environment and evidence

**AP-27 Tool assumption.** Mistake: assuming a tool the skill mentions is installed. Result: the first command fails, you backtrack, and the agent often invents the result instead of using a fallback.
- Fix: before the first use, test each tool: `command -v <tool>`. Write the fallback order into the skill (bundled script, then MCP tool, then manual method) and say which one ran.
- Check: a "command not found" appears mid-run.

**AP-29 Path confusion (create vs revise).** Mistake: writing test steps for the wrong case. For a new skill, a trigger test "passes" because the skill is not installed. For a revision, tests that only try the new text miss regressions against the old version.
- Fix: state at the top of the plan which path you are on. New skill: install it, confirm it appears in the `/` menu, then run trigger tests, with a no-skill baseline for comparison. Revision: keep a copy of the old version and run the same prompts against both.
- Check: every trigger test passes but you never confirmed the skill was installed. Run `/agentic-maker:derail <skill-dir>` to see what fresh agents actually did.

## Research

**AP-28 Quality blindness.** Mistake: treating every example skill you collect as a good model. Result: the comparison has only positive rows, so the weak patterns get copied.
- Fix: rate each example (strong, usable, weak) and give every weak one an "avoid" note naming the pattern.
- Check: your comparison has no "avoid" entries.

**AP-30 Research scope creep.** Mistake: collecting and reading 20 or more examples with no stopping rule. Result: the budget goes to discovery and the comparison is broad and shallow.
- Fix: before searching, set a budget (for example 10 examples, 3 steps). Stop as soon as you hold 3 usable examples to compare, then compare them in depth.
- Check: more than 10 examples collected, or more than 3 steps spent on research alone.

## Evidence for rules and tone

**AP-32 Discipline skill without a baseline.** Mistake: writing a rule-enforcing skill (test first, verify before merge, read before synthesis) from excuses you imagined. Result: the skill triggers, then agents get around it with excuses you did not predict.
- Fix: run a pressure scenario with no skill, that adds pressure (for example a deadline). Copy the agent's excuses word for word. Write one counter per excuse into the skill. Run again with the skill and confirm each counter holds.
- Check: no saved baseline run, or the guardrail says only "do not cheat" or "follow the process".

**AP-33 Persuasion mismatch.** Mistake: "we" language in a rule-enforcing skill, or "YOU MUST" everywhere in a guidance skill. Result: "we" reads as "the rule bends for us"; constant shouting makes every judgment call feel optional, so the whole skill gets ignored.

| Skill type | Tone |
|---|---|
| Discipline (must not be skipped) | firm authority, plus a commitment ("announce which step you are on") |
| Guidance (judgment calls) | moderate authority, plus shared goals |
| Collaborative (brainstorm, design) | shared goals, plus a commitment |

- Check: a discipline skill reads like an invitation, or a guidance skill reads like an interrogation.

## Rigidity

**AP-34 Uniform freedom level.** Mistake: the whole skill is equally strict or equally loose. Result: strict everywhere wastes judgment on easy steps; loose everywhere leaves the agent guessing install commands and validation scripts.
- Fix: choose per step by what breaks if the agent deviates.

| Step | Freedom | Write it as |
|---|---|---|
| Install, validate, anything with one correct command | low | exact command and expected output |
| Workflow shape | medium | ordered steps with named outputs, wording is free |
| Choosing an approach | high | the goal and the criteria, no script |

- Check: read the skill top to bottom; if it sounds the same everywhere, redo the table above for each step.
