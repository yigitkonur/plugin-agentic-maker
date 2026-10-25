# Test a skill with fresh agents (RED, GREEN, REFACTOR)

> Read when: you finished a draft skill (or changed one) and need to know whether fresh agents choose it and follow it, before you ship it.

Run the skill's text through agents that have never seen it. Two questions, in this order: does a fresh agent choose the skill (trigger), and once chosen, does it do what the text says (following). Write nothing until you have watched the failure it must fix.

## Which skills need the full cycle

| Skill | Run |
|---|---|
| Rules an agent can skip under pressure (verify before done, research before writing, tests first) | RED, GREEN, REFACTOR, then trigger tests |
| Reference or format guide, no rule to break | Trigger tests, plus one RED run to see what the agent gets wrong alone |
| `disable-model-invocation: true` | RED, GREEN, REFACTOR only. A worker cannot choose it, so a trigger test cannot observe it; start it with `/<plugin>:<skill>` |

## RED: watch fresh agents fail without the skill

1. Copy the project to a scratch folder. In the copy, cut the skill's `SKILL.md` down to its frontmatter and delete `references/` and `scripts/`. The agent sees the name and description and nothing else.
2. Write 3 scenarios in `.agentic-maker/scenarios/` (format: `skills/derail/references/scenarios.md`): a normal task, an ambiguous one, one with a missing input. Each prompt reads like a user's request and never names the skill.
3. For a discipline skill, put 3 or more pressures in the prompt: a deadline, hours already spent, an authority asking to skip the step, a tired user. One pressure is usually resisted; three together expose the gap. Start with the single hardest scenario.
4. Add receipts that check the disk, not the agent's words (`exists:`, `regex:`, `cmd: ... => 0`). A take whose receipts fail is a failure whatever the agent said.
5. Preview, then run: `agentic-maker run <scenario> --dry-run`, then `agentic-maker run <scenario>`. Run 3 takes per scenario; one take shows one path, not a rate.
6. Read each take with `/agentic-maker:derail <scratch skill dir>` (it spawns the trace reader). Keep each wrong action and the agent's own words for it, quoted verbatim. "I already checked it by hand" and "the user is in a hurry" are different causes and need different text.

The RED output is a list: scenario, wrong action, quote, receipt that failed. No such list, no GREEN.

## GREEN: write the least text that fixes what you saw

1. Restore the full skill folder in the scratch copy.
2. Write only the instructions that remove a listed failure. Do not add text for failures nobody observed.
3. Rerun the same scenarios, 3 takes each, in fresh sessions. Check `env.json` in the take folder: the skill must appear in the listing the worker saw. A pass in a run where the skill never loaded proves nothing.
4. Passing: every receipt passes in 3 of 3 takes, and the trace shows the agent opened the skill and followed the step that was failing.

## REFACTOR: close the loopholes by fixing the text

Rerun with new variants: other wording, other pressures, another input. When a take drifts:

1. Find the sentence the agent followed instead of your intent (the reader names it, with a root-cause code; vocabulary in `skills/derailment-method`).
2. Rewrite or delete that sentence. Do not add a do/do-not line or an "excuses" table beside it: the original sentence still reads as permission, and `agentic-maker check diff` flags an edit that adds a rule while the cause text is unchanged.
3. Rerun in a fresh session and confirm with `agentic-maker check predicate`. A fix counts only when a take that ran after it passes.

The pattern list is in `skills/derailment-method/references/fix-patterns.md`; the whole loop with its ledger is `/agentic-maker:derail`. Do not ask the agent "how could this skill be clearer?" as a test. Its answer is a guess; the trace is the evidence.

## Trigger tests: should-fire and should-stay-quiet

Write the prompts as users type them, never naming the skill. The description rules are in `skills/agent-interface-design/references/skill/descriptions-that-trigger.md`. Make 3 lists:

- 5 or more should-fire prompts, 3 or more of them paraphrases (different verbs and nouns, same job).
- 5 or more should-stay-quiet prompts: adjacent tasks a neighbour skill owns, and plain unrelated requests.

Turn a scenario that passed into a case, then add the rest by hand:

```
agentic-maker eval-emit <scenario> --out evals
claude plugin eval <plugin dir> --scaffold --case <scenario> --runs 10 --threshold 0.9
```

- Positive case: a grader `type: tool_used`, `tool: Skill` with an `input_match` on your skill name (`eval-emit` writes it; see `evals/triggers-skill-write/graders/skill-fired.md`).
- Negative case: the same grader with `min: 0` and `max: 0`, so any Skill call fails it (copy `evals/ignores-react-form/graders/no-skill.md`).
- `claude plugin eval` also runs a no-plugin arm. Under it, `tool_used: Skill` graders are a plugin-fired indicator, not part of the score, so read the delta between the two arms for the effect of the plugin.
- `--scaffold` runs the case's setup script as you; use it only on cases you wrote or emitted yourself.
- The plugin must be loaded by the eval. An unloaded skill never fires, so a negative case passes by default; run the positive case first.
- For the crowd effect (a neighbour winning), also run one scenario with `isolation: in-situ`.

## Functional check and revisions

Trigger tests only show the skill loads. Also run one full primary workflow end to end, one bad-input case and one empty-input case, and check the output the skill promises. For a changed skill, run the same trigger prompts against the old and the new text, and add prompts for any scope you changed.

## What a pass looks like

| Check | Pass |
|---|---|
| Should-fire prompts | 90% or more fire the skill, at least 10 runs per prompt |
| Should-stay-quiet prompts | 0% fire it, same run count |
| Discipline scenarios, with the skill | every receipt passes in 3 of 3 takes |
| Same scenarios, without the skill (RED) | at least one receipt fails, otherwise the skill adds nothing |
| End of REFACTOR | no P0 or P1 finding, receipts pass, 2 consecutive clean takes |

One sample proves little. Agents are not deterministic: 1 of 1 passing is compatible with a 50% rate. Report counts ("fired 9 of 10, 0 of 10 on the quiet set"), the number of takes, and what was not run. If you could not rerun after a fix, say the fix is unverified.

Hand off: `/agentic-maker:derail <skill dir>` runs the loop above; `/agentic-maker:audit <skill dir>` runs read-only probes on the skill; `agentic-maker scan skill` locates skills in a project.
