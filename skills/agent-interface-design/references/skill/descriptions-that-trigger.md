# Skill descriptions that get chosen

> Read when: you write or review a skill's `name` and `description`, or a derailment run shows the skill was never chosen (T1), the wrong one won (T2), or it fired on the wrong request (T3).

The description is the only thing an agent has when it decides whether to open a skill: it sits in a listing next to dozens of others. Everything else in the skill is invisible until it is chosen. Treat the description as the skill's interface.

## What worked and what failed (observed)

A skill named `manifest-synth` with the description "Synthesizes semver-delimited artefact manifests from VCS delta enumerations for downstream distribution channels" was run against the request "put together the release notes from commits.txt". Across takes it was chosen in some and not in others; in one the worker wrote, of the skill it had seen, that plain release notes did not need it. The same skill with its description rewritten in the words of the request was chosen in every following take.

## Rules

1. **Lead with the job, in the words a user types.** "Use when asked to write release notes or a changelog from a list of commits" beats a description of the mechanism. Include the obvious synonyms (release notes, changelog, version summary).
2. **Name the trigger situations, then the output.** What the user has, what they want, what the skill produces.
3. **Say what it is not for**, in a clause, when a neighbour is easy to confuse with it ("not for human-facing UI").
4. **No jargon the user would not say.** If the description needs a glossary, the agent does not match it.
5. **Make the `name` informative.** A listing shows the name too; an opaque name removes half the signal. (A good name can mask a bad description in a test with one skill and fail in a crowd.)
6. **Keep it short** - about 200 to 300 characters. Every always-on description is paid for in every session; a user-started skill (`disable-model-invocation: true`) costs almost nothing in context but should still read well in the menu.
7. **Do not name an event the model cannot know.** Write "when the user asks ..." not "when the build fails" unless the skill is meant to react to that.

## Test it, do not argue about it

- Write a scenario whose prompt is an everyday request and never names the skill (`skills/derail/references/scenarios.md`). Run several takes: the rate at which the skill is chosen is the measurement.
- Run it once with the user's real skills installed (`isolation: in-situ`): collisions (T2) only show up in a crowd.
- Keep a trigger test in CI with `claude plugin eval`: a positive case (`tool_used: Skill`), a negative case (an unrelated request must not use it), and the no-plugin baseline for the difference. `agentic-maker eval-emit <scenario>` writes the positive case from a scenario that already passed.

## Fix patterns

| Defect | Fix |
|---|---|
| T1 not triggered | rewrite the description in user words; make the name informative |
| T2 a neighbour won | state what this skill does that the neighbour does not; remove overlapping phrases from both |
| T3 fired on the wrong request | add the negative clause; tighten the verbs |
