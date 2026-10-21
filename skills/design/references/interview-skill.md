# New skill interview

> Read when: the surface chosen in step 1 is a skill (a SKILL.md an agent reads), and you are about to ask the user what it must do.

Paths in this file are relative to `${CLAUDE_PLUGIN_ROOT}/skills/agent-interface-design/references/`. Ask in these words, one group of up to four at a time. The closed ones go through `AskUserQuestion` with the options listed; the open ones are plain text. A skill is judged by a run of a fresh agent, so the interview ends in a scenario, not in a text.

## Group 1: why it should exist

1. **The failure (open).** "What does an agent get wrong today without this? Give one real case: what it did, what you wanted."
2. **The words (open).** "How would you ask for this in a normal message? Give two or three phrasings." These become the description and the first scenario's prompt; the description starts from them (`skill/descriptions-that-trigger.md`).
3. **Who starts it (closed).** Options: the model, when the task fits; only the user, by a slash command (`disable-model-invocation: true`: use it for anything with side effects or cost); both.
4. **What it changes (closed, several).** Options: reads only; writes files; runs commands; calls the network or spends money. Anything past "reads only" is named in the skill's `allowed-tools`.

## Group 2: what it contains

5. **Steps (open).** "List the steps in order, and say which ones the agent tends to skip."
6. **Needs a script or a reference (closed).** Options: neither, plain instructions; a script for something deterministic (a count, a parse); reference files for detail the agent reads only when it needs it (`skill/text-as-program.md`).
7. **Harness (closed).** Options: Claude Code; Codex; several. Paths and tool names in the text are written for them.
8. **Proof (open).** "What would a correct result look like on disk? That becomes the receipts of the scenario."

## Then

Sketch the frontmatter and the section outline, not the full text, and write the three scenarios (a normal task, an ambiguous one, a failure) from [scenarios](../../derail/references/scenarios.md). Wait for the user's approval. Once the skill is written, `/agentic-maker:derail <skill>` is the check: it shows whether it is chosen, read and followed.
