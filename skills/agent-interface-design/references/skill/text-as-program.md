# A skill is a program an agent executes

> Read when: you write or fix the body of a skill, its references and scripts, or a derailment run shows the agent guessing, skipping a step or taking a wrong path.

An agent follows a skill literally. Where the text is vague it guesses; where a path is wrong it hunts; where a step has no check it skims. These rules come from the root causes found in real runs (taxonomy in `derailment-method`).

## Write it so the right path is the natural one

- **Give exact paths and commands, from where the agent will stand.** A relative `scripts/run.py` that is relative to the skill directory fails when the agent's working directory is the user's project. Use the skill's directory variable (`${CLAUDE_SKILL_DIR}` in a Claude Code skill) or say "relative to this skill's directory". Check every reference path against the file tree; one letter (`reference/` for `references/`) cost a real run three extra tool calls.
- **Replace adjectives with numbers.** "Keep entries short" became "at most 72 characters including the PR number" and the variation disappeared.
- **State the output format once, where the agent writes it.** Inline small schemas (ten items or fewer); cross-reference larger ones by exact section name.
- **Put a check on every phase.** A step the agent can finish without evidence is a step it will skip. Name the command and the expected result.
- **Route, do not dump.** `SKILL.md` carries the decision and a "read X when Y" table; each reference holds one decision. A reference that no row points to is never read (S4).
- **Surface prerequisites before step 1** with a command that tests for them.

## Injected commands and hooks (Claude Code, verified 2026-10-20)

- A failing `` !`command` `` in a skill aborts the whole invocation, silently: an empty result in zero turns. End every injected command with `|| true` and keep it read-only.
- `$ARGUMENTS`, `${CLAUDE_SKILL_DIR}`, `${CLAUDE_SESSION_ID}` and `${CLAUDE_PLUGIN_ROOT}` are substituted in skill content. Hook commands in a skill's frontmatter run only after the skill is invoked and stay registered for the session.
- A `context: fork` skill has no conversation history and cannot ask the user; put everything it needs in its arguments.
- `allowed-tools` pre-approves commands for the turn; it does not widen the user's permission rules, and a command with shell variables or chained operations cannot be matched against a pattern and is refused. Tell the agent to run one command per call with literal paths.

## What a test run looks like

Run the skill on an everyday task with fresh agents and read the whole execution (`/agentic-maker:derail`). Expect two kinds of finding: text that misled (fix the text) and a harness that hid something (fix the harness: a sandbox that blocks the skill's own reference files is not a skill defect).
