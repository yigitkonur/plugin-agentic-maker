# A skill that coordinates MCP tools

> Read when: a skill must call tools from one or more MCP servers, and you are deciding how to name the tools, order the calls, handle a missing server, and keep the skill from restating the tool descriptions.

The server gives the agent tools. The skill gives it the order, the rules and the stop conditions the tools do not carry. Write only the second part.

## Name each tool exactly

The agent calls a tool by its full name. A skill that says "use the search tool" makes it guess among every connected server.

| Server source | Full tool name |
|---|---|
| User or project server named `linear` | `mcp__linear__create_issue` |
| Server bundled in plugin `my-plugin`, server key `db` | `mcp__plugin_my-plugin_db__query` |

Characters outside `A-Z a-z 0-9 _ -` in a plugin or server name become `_`. Copy the name from the tool list of a session where the server is connected; do not build it from memory.

- Write the server and the tool in backticks every time: `linear` / `create_issue`, then the full name once in a table at the top of the skill.
- If the skill grants tools with `allowed-tools`, list the full names. Granting only pre-approves the tools for that turn; it does not restrict other tools and does not connect the server.
- Tool search is on by default, so MCP tool schemas may not be loaded when the skill starts. Add one line before step 1: "If `mcp__linear__list_issues` is not callable, load it with ToolSearch (`select:mcp__linear__list_issues`)."
- Bind the skill to a tool name you checked. A renamed tool breaks the call; pin the server version in the setup note and re-check names when it changes.

## Order the calls

List the 2 or 3 workflows users run most on the server. Write each as a numbered list of calls with the data each one hands to the next.

```
1. `linear` / `list_projects` -> keep `project_id`
2. `linear` / `list_issues` (project_id, state="unassigned") -> keep `issue_ids`
3. `linear` / `update_issue` for each id (assignee, labels)
Check: `list_issues` with the same filter returns 0 items.
```

- Say which output field feeds which input. IDs and URLs are the usual hand-offs; name them.
- Put a check after every phase that writes, naming the read call and the expected result. Validate each output before it feeds the next call, so one bad value does not cascade.
- Spanning several servers: one phase per server, each phase ends with the values the next one needs. On failure in phase N, stop, report what phases 1 to N-1 already changed, and offer retry or skip. Do not roll back unless the skill lists the undo call. Have the run log the chain of calls and the IDs and URLs captured, so a failure can be traced end to end.
- Bulk work: state the page size and a cap (for example 50 items per call, at most 5 calls) so the agent does not loop on a rate limit.

## Handle a missing server

A skill gets loaded whether or not its server is connected. Test for it first and stop early.

1. Step 0 names a cheap read call that proves the server answers (`linear` / `list_teams`, limit 1).
2. If the tool is not in the tool list, say so in one sentence: the server `linear` is not connected. Give the exact fix: `claude mcp list` shows its state, `/mcp` reconnects it, `claude mcp add` registers it.
3. If a call returns empty where data must exist, ask the user to verify the workspace or project. If it fails on auth (401, 403), tell the user which scope or login is missing, and treat expired tokens as a normal case, not a surprise. Do not retry the same call.
4. Offer the fallback only if one exists (see below). Otherwise end the run; do not improvise with web search.

Version note: failed servers are reported to the agent only when tool search is on. With it off the agent sees nothing, so step 0 matters more.

### Fallback shape

| Case | Layout |
|---|---|
| Skill is useless without the server | Stop at step 0 with the fix above |
| Work can be done by hand | `SKILL.md` holds the shared steps; `references/<manual-path>.md` holds the manual path; `references/<tool-path>.md` holds the tool path. Step 0 picks one |
| Users may swap services | Keep `SKILL.md` generic (rules, order, checks); put tool names in one `references/<service>.md` per service |

Embed tool names in `SKILL.md` only when the team always uses that one service.

## Do not copy the tool descriptions

The agent already sees every tool's description and schema. Copying them costs context and goes stale on the next server release.

- Drop: parameter lists, type tables, what the tool "does".
- Keep: the order, the values to pass that the schema leaves open (`state="unassigned"`), business rules ("split tasks over 8 points"), naming conventions, duplicate checks before a create, and the error cases that need a decision.
- Error text: map the two or three failures that need a human decision to one sentence each. Leave the rest to the server's own message.
- If the descriptions are wrong or unclear, fix the server, not the skill: see `skills/agent-interface-design/references/mcp/descriptions-names-and-routing.md` and `skills/agent-interface-design/references/mcp/errors-framing-and-recovery.md`. Building, hosting and testing the server side starts at `skills/agent-interface-design/references/mcp/quick-reference.md`.

## Description and test

- Name the service and the jobs in the skill description, in the user's words ("Linear", "sprint", "create tickets"). Rules: `skills/agent-interface-design/references/skill/descriptions-that-trigger.md`.
- Make every step runnable as written: `skills/agent-interface-design/references/skill/text-as-program.md`.
- Test in two runs. First ask the agent to call one server tool with no skill (`Use the Linear MCP to list my projects`); if that fails, the problem is the connection. Then run the skill on an everyday request and read the execution with `/agentic-maker:derail <skill-dir>`. Also run it once with the server disconnected and check that step 0 stops with the fix.
