---
name: build-mcp
description: Build, extend or repair an MCP server for agents, probe it, hand over the test. Started by you.
disable-model-invocation: true
argument-hint: "<what the server should let an agent do | path of a server to extend or repair>"
allowed-tools: Bash(agentic-maker *) Bash(${CLAUDE_PLUGIN_ROOT}/bin/agentic-maker *) Read Grep Glob Write Edit
---

# Build an MCP server for agents

Request: `$ARGUMENTS`

The caller is a model that reads tool names and descriptions, fills a schema, and acts on the answer. This skill decides the tools and checks the result; it does not carry SDK code, so write the implementation with the SDK's own documentation (or a companion builder skill, only if installed: [companion-routing.md](../agent-interface-design/references/decisions/companion-routing.md)). Pages are under `${CLAUDE_PLUGIN_ROOT}/skills/agent-interface-design/references/mcp/`. This runs in the main conversation: ask the user directly, and only what changes the result.

## Pick the mode

| The request is | Do |
|---|---|
| a new server | steps 1-7 |
| add a tool to a server (a path, relative to the current working directory, not to the plugin) | `ls` it and read the existing tools first and match their conventions; step 3 for the one tool, then 4-7 |
| a server to optimize or repair (a path) | baseline probe from step 4, read the findings, then 3-7 on what they found |

## Steps

1. **Scope.** Is MCP the right surface at all ([surface-choice.md](../agent-interface-design/references/decisions/surface-choice.md))? Who authenticates, local or remote, which operations change or delete things. For a new server run the interview in [interview-mcp.md](../design/references/interview-mcp.md) one group at a time and follow [mcp-design-workflow.md](../design/references/mcp-design-workflow.md); no code until the user agrees to the sketch.
2. **Ground it.** What each tool wraps (an API, a database, a service) is read from its real docs and real responses, not memory. Every name, field and value in a tool comes from there; one found nowhere goes in the report as a suggestion. If the `research` plugin is installed use `/research:ask`; if you can verify nothing, say so.
3. **Design each tool from a user intent, then write it.** One tool per task the user wants done, not per endpoint ([design-intent-based-tools.md](../agent-interface-design/references/mcp/design-intent-based-tools.md)); stay under about 20 tools ([tool-count.md](../agent-interface-design/references/decisions/tool-count.md)).
   - Name and description: verb plus resource, says when to use it, about 100 tokens ([descriptions-structure-and-length.md](../agent-interface-design/references/mcp/descriptions-structure-and-length.md)).
   - Schema: flat, at most about six required parameters ([schemas-flat-and-sized.md](../agent-interface-design/references/mcp/schemas-flat-and-sized.md)).
   - Answer: curated for a model, not the upstream JSON ([responses-curated-and-semantic.md](../agent-interface-design/references/mcp/responses-curated-and-semantic.md)).
   - Failure: a tool error the model can act on, with the next call to make ([errors-protocol-vs-tool.md](../agent-interface-design/references/mcp/errors-protocol-vs-tool.md)); validate input on the server.
   - Safety: mark read-only and destructive tools with annotations and make a destructive one ask for confirmation ([least-privilege-and-confirmation.md](../agent-interface-design/references/mcp/security/least-privilege-and-confirmation.md)).
   - A stdio server writes nothing but protocol to stdout ([ops-stdio-hygiene.md](../agent-interface-design/references/mcp/ops-stdio-hygiene.md)).
4. **Probe after each tool.** Run each check as its own Bash call, with no `&&`, `;` or heredoc; a denied call skips only that check, and Read, Grep and Glob are the fallback. `agentic-maker probe mcp "<the command that starts the server>"` lists the tools over the protocol and checks names, descriptions, schemas, annotations and size. Add `--call 'tool={"arg":"value"}'` only for read-only tools. Each finding names the page with the fix. Fix, probe again, stop when no High finding is left.
5. **One live route.** Exercise the server through a real client (the MCP Inspector, or `mcpc` if installed) and say which one you used.
6. **Hand over the test.** Only the user can start `/agentic-maker:derail`; you cannot, so do not try. Write three scenarios into `.agentic-maker/scenarios/<name>.md` (format in `${CLAUDE_PLUGIN_ROOT}/skills/derail/references/scenarios.md`, `kind: mcp`): a task that needs two tools, an ambiguous one, and one that tempts the agent to a destructive call. Receipts run your probe on the result and check the tool list, not the agent's words. Preview one with `agentic-maker run <name> --dry-run`, and end by giving the user the exact command `/agentic-maker:derail <server command>`. Until they run it the server is untested, and your report says so.
7. **Ship.** The final message is a table with one row per rule in [hard-rules.md](../agent-interface-design/references/mcp/hard-rules.md), marked checked (the command and its output, or the file and line you read) or unchecked, followed by what you probed and what you handed over. Authenticated servers are not probed; say so if that applies. A message without that table is not a ship.

## Do this, not that

| Do | Not |
|---|---|
| One tool per user intent | One tool per endpoint |
| Probe after every tool | Write ten tools, then probe once |
| Fix the description or answer that misled the agent | Add a "do not" note beside it |
| Say what you could not verify | Present a guess as a fact |
