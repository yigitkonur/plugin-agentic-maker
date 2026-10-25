---
name: build-skill
description: Create, redesign or merge a skill, grounded in facts, then hand over the test. Started by you.
disable-model-invocation: true
argument-hint: "<what the skill should do | path of a skill to redesign>"
allowed-tools: Bash(agentic-maker *) Bash(${CLAUDE_PLUGIN_ROOT}/bin/agentic-maker *) Bash(claude plugin validate *) Read Grep Glob Write Edit
---

# Build a skill

> In Codex: `$ARGUMENTS` is what the user wrote after the skill name. `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_SKILL_DIR}` mean the plugin folder and this skill's folder (the plugin folder is two levels above this file); `agentic-maker` is on PATH or is `<plugin folder>/bin/agentic-maker`. A line that starts with an exclamation mark and a backtick is a command: run it yourself first.

Request: `$ARGUMENTS`

Pages are in `${CLAUDE_SKILL_DIR}/references/` (listed at the end); the two skill pages in the knowledge base are `${CLAUDE_PLUGIN_ROOT}/skills/agent-interface-design/references/skill/`. Open a page when the step names it, not before. This runs in the main conversation, so ask the user directly, and only what changes the result.

## Pick the mode

| The request is | Do |
|---|---|
| a new skill | steps 1-7 |
| an existing skill to redesign (a path, relative to the current working directory, not to the plugin) | `ls` that path in the current directory and read it first. If the user has derail findings for it, read them; they say how it fails today. Then steps 3-7 |
| several skills or sources to merge | step 2 builds a comparison table (what to inherit, what to drop, why) before any text is written. Every command, flag and path comes verbatim from a source; one found in no source goes in the report as a suggested addition, not in the skill |
| "turn this conversation into a skill" | list what was done as a nested outline, five levels at most: milestone, phase, step, error met and its correction, invariant learned. Corrections and invariants become the skill's rules; repeated commands become scripts. Then steps 2-7 |

## Steps

1. **Scope.** Who invokes it (the model on a matching request, or only the user), in which harnesses it must run, and one sentence for what changes for the agent when it is loaded. [naming-and-boundaries.md](references/naming-and-boundaries.md) if one skill or two.
2. **Ground it.** For any non-trivial domain, gather verified facts first: the official docs, the real command output, the API as it is today. If the `research` plugin is installed use `/research:ask` (one question) or `/research:deep` (five or more sources); otherwise use whatever web and file tools you have. A skill drafted from memory carries the model's guesses into every future run; if you can verify nothing, say so and stop. Look at two or three existing skills for the same job and note what each does well.
3. **Lay it out before writing.** What stays in `SKILL.md` (under 500 lines), what goes to `references/`, what becomes a script: [references-and-scripts.md](references/references-and-scripts.md). Pick the body's shape: [workflow-patterns.md](references/workflow-patterns.md). Show the layout to the user when the request was open-ended.
4. **Write it.**
   - Frontmatter: [frontmatter.md](references/frontmatter.md). Portable fields only if it must run outside Claude Code.
   - Description: it is the only thing the model sees when deciding to load the skill. [descriptions-that-trigger.md](../agent-interface-design/references/skill/descriptions-that-trigger.md).
   - Body: exact paths and commands, numbers instead of adjectives, a check on every phase, using only commands and flags that appear in the sources from step 2: [text-as-program.md](../agent-interface-design/references/skill/text-as-program.md). How strict each step should be: [instruction-strength.md](references/instruction-strength.md).
   - A skill that drives MCP tools: [wrapping-mcp-tools.md](references/wrapping-mcp-tools.md).
5. **Check what a script can check.** Run each check as its own Bash call, with no `&&`, `;` or heredoc: `claude plugin validate <skill dir>` (frontmatter and structure), `wc -l <skill dir>/SKILL.md`, every bundled script on real input. A denied call skips only that check: redo it with Read, Grep or Glob (frontmatter fields, line count, each link and path) and name the denied command in the report. Then open [checklist.md](references/checklist.md) and build a table with one row per line, marked checked or unchecked.
6. **Hand over the test.** Only the user can start `/agentic-maker:derail`; you cannot, so do not try. Write three scenarios into `.agentic-maker/scenarios/<name>.md` (format in `${CLAUDE_PLUGIN_ROOT}/skills/derail/references/scenarios.md`): a normal request in the user's words that never names the skill, an ambiguous one, and one with a missing input; each with receipts that check the disk, not the agent's words. Preview one with `agentic-maker run <name> --dry-run`. End by giving the user the exact command, `/agentic-maker:derail <skill dir>`. Until they run it the skill is untested, and your report says so. Procedure and what a pass looks like: [test-with-fresh-agents.md](references/test-with-fresh-agents.md). A skill only the user can start is tested through a slash-command prompt; the derail dry-run says so.
7. **Ship.** The final message is the checklist table from step 5: one row per line of [checklist.md](references/checklist.md), marked checked (with the command and its output, or the file and line you read) or unchecked. A message without that table is not a ship.

## Do this, not that

| Do | Not |
|---|---|
| Verify every API, flag and path against the real thing | Write them from memory |
| Fix the sentence that misled the agent | Add a "never do X" rule next to it |
| Keep `SKILL.md` as the routing and the rules; move bulk to references | Paste a 1,500-line guide into one file |
| Write scripts in Python or Node and run them before you ship | Ship a script you never ran |
| Report what you could not verify | Present a guess as a fact |

## Pages

| Open | When |
|---|---|
| [frontmatter.md](references/frontmatter.md) | writing or fixing frontmatter |
| [naming-and-boundaries.md](references/naming-and-boundaries.md) | naming it, splitting or merging |
| [references-and-scripts.md](references/references-and-scripts.md) | deciding what goes where |
| [workflow-patterns.md](references/workflow-patterns.md) | choosing the structure of the body |
| [instruction-strength.md](references/instruction-strength.md) | a step is too loose or too rigid |
| [wrapping-mcp-tools.md](references/wrapping-mcp-tools.md) | the skill calls MCP tools |
| [test-with-fresh-agents.md](references/test-with-fresh-agents.md) | step 6 |
| [checklist.md](references/checklist.md) | before shipping |
| [troubleshooting.md](references/troubleshooting.md) | it does not load, trigger or behave |
| [anti-patterns-content.md](references/anti-patterns-content.md), [anti-patterns-process.md](references/anti-patterns-process.md) | reviewing a draft or your own process |
| [worked-examples.md](references/worked-examples.md) | you want a structure to copy |
