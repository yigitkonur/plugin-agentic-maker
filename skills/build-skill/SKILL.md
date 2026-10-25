---
name: build-skill
description: Create, redesign or merge an agent skill: ground it in verified facts, lay it out, write it, then test it with fresh agents. Started by you.
disable-model-invocation: true
argument-hint: "<what the skill should do | path of a skill to redesign>"
allowed-tools: Bash(agentic-maker *) Bash(${CLAUDE_PLUGIN_ROOT}/bin/agentic-maker *) Bash(claude plugin validate *) Read Grep Glob Write Edit
---

# Build a skill

Request: `$ARGUMENTS`

Pages are in `${CLAUDE_SKILL_DIR}/references/` (listed at the end); the two skill pages in the knowledge base are `${CLAUDE_PLUGIN_ROOT}/skills/agent-interface-design/references/skill/`. Open a page when the step names it, not before. This runs in the main conversation, so ask the user directly, and only what changes the result.

## Pick the mode

| The request is | Do |
|---|---|
| a new skill | steps 1-7 |
| an existing skill to redesign (a path) | read it first, run `/agentic-maker:derail <path>` on a scratch copy to see how it fails today (that is the RED of step 6), then steps 3-7 |
| several skills or sources to merge | step 2 builds a comparison table (what to inherit, what to drop, why) before any text is written |
| "turn this conversation into a skill" | list what was done as a nested outline, five levels at most: milestone, phase, step, error met and its correction, invariant learned. Corrections and invariants become the skill's rules; repeated commands become scripts. Then steps 2-7 |

## Steps

1. **Scope.** Who invokes it (the model on a matching request, or only the user), in which harnesses it must run, and one sentence for what changes for the agent when it is loaded. [naming-and-boundaries.md](references/naming-and-boundaries.md) if one skill or two.
2. **Ground it.** For any non-trivial domain, gather verified facts first: the official docs, the real command output, the API as it is today. If the `research` plugin is installed use `/research:ask` (one question) or `/research:deep` (five or more sources); otherwise use whatever web and file tools you have. A skill drafted from memory carries the model's guesses into every future run; if you can verify nothing, say so and stop. Look at two or three existing skills for the same job and note what each does well.
3. **Lay it out before writing.** What stays in `SKILL.md` (under 500 lines), what goes to `references/`, what becomes a script: [references-and-scripts.md](references/references-and-scripts.md). Pick the body's shape: [workflow-patterns.md](references/workflow-patterns.md). Show the layout to the user when the request was open-ended.
4. **Write it.**
   - Frontmatter: [frontmatter.md](references/frontmatter.md). Portable fields only if it must run outside Claude Code.
   - Description: it is the only thing the model sees when deciding to load the skill. [descriptions-that-trigger.md](../agent-interface-design/references/skill/descriptions-that-trigger.md).
   - Body: exact paths and commands, numbers instead of adjectives, a check on every phase: [text-as-program.md](../agent-interface-design/references/skill/text-as-program.md). How strict each step should be: [instruction-strength.md](references/instruction-strength.md).
   - A skill that drives MCP tools: [wrapping-mcp-tools.md](references/wrapping-mcp-tools.md).
5. **Check what a script can check.** `claude plugin validate <skill dir>` (frontmatter and structure); run every bundled script on real input; open each link and path. [checklist.md](references/checklist.md) lists the rest.
6. **Test it with fresh agents.** `/agentic-maker:derail <skill dir>`: a clean-room agent gets a realistic request that never names the skill, a reader finds where it drifted, and the text that caused each drift is fixed and rerun. Do it on a scratch copy of a skill you do not own. Procedure and what a pass looks like: [test-with-fresh-agents.md](references/test-with-fresh-agents.md). A skill only the user can start is tested through a slash-command prompt; the derail dry-run says so.
7. **Ship.** Go through [checklist.md](references/checklist.md) and say which lines you checked and how. Anything unchecked goes in the report as unchecked.

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
