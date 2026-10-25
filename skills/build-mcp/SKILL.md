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
| a server to optimize or repair (a path) | baseline probe from step 4, read the findings, then 3-7 on what they found. Edit only the server file you were given: a helper or loop file beside it (`_mini.py`, a vendored base) is read-only, so fix a finding that comes from it in the server file or report it |

## Steps

Bash runs one `agentic-maker ...` command per call: no `&&`, `;`, heredoc or shell function. Create and edit files with Write and Edit (Write creates missing directories). If a call is denied, do not retry it in another form (`sh -c`, a pipe) and name it in the report; a denied call skips only that check, and Read, Grep and Glob are the fallback.

1. **Scope.** Is MCP the right surface at all ([surface-choice.md](../agent-interface-design/references/decisions/surface-choice.md))? Who authenticates, local or remote, which operations change or delete things. For a new server run the interview in [interview-mcp.md](../design/references/interview-mcp.md) one group at a time and follow [mcp-design-workflow.md](../design/references/mcp-design-workflow.md); no code until the user agrees to the sketch.
2. **Ground it.** What each tool wraps (an API, a database, a service) is read from its real docs and real responses, not memory. Every name, field and value in a tool comes from there; one found nowhere goes in the report as a suggestion. If the `research` plugin is installed use `/research:ask`; if you can verify nothing, say so.
3. **Design each tool from a user intent, then write it.** One tool per task the user wants done, not per endpoint ([design-intent-based-tools.md](../agent-interface-design/references/mcp/design-intent-based-tools.md)); stay under about 20 tools ([tool-count.md](../agent-interface-design/references/decisions/tool-count.md)).
   - Name and description: verb plus resource, says when to use it, about 100 tokens ([descriptions-structure-and-length.md](../agent-interface-design/references/mcp/descriptions-structure-and-length.md)).
   - Schema: flat, at most about six parameters in all, required or not, which is what the probe counts. Past that, split the tool by intent or group optional fields; do not delete a capability to clear a finding, and list any parameter you drop in the report ([schemas-flat-and-sized.md](../agent-interface-design/references/mcp/schemas-flat-and-sized.md)).
   - Answer: curated for a model, not the upstream JSON ([responses-curated-and-semantic.md](../agent-interface-design/references/mcp/responses-curated-and-semantic.md)).
   - Failure: a tool error the model can act on, with the next call to make ([errors-protocol-vs-tool.md](../agent-interface-design/references/mcp/errors-protocol-vs-tool.md)); validate input on the server.
   - Safety: mark read-only and destructive tools with annotations and make a destructive one ask for confirmation ([least-privilege-and-confirmation.md](../agent-interface-design/references/mcp/security/least-privilege-and-confirmation.md)).
   - Stdout carries protocol only: a banner or log line in your own server file is removed or sent to stderr ([ops-stdio-hygiene.md](../agent-interface-design/references/mcp/ops-stdio-hygiene.md)).
4. **Probe after each tool.** `agentic-maker probe mcp "<the command that starts the server>"` lists the tools over the protocol and checks names, descriptions, schemas, annotations and size. Add `--call 'tool={"arg":"value"}'` only for read-only tools. A tool the request names as off-limits (export, delete, anything) is never passed to `--call`, whatever its annotation says. Each finding names the page with the fix. Fix, probe again, stop when no High finding is left.
5. **One live route.** Call the simplest read-only lookup the request has not ruled out with `agentic-maker probe mcp "<server command>" --call 'tool={"arg":"value"}'`; that is the live route and it needs no extra permission. The MCP Inspector and `mcpc` are outside the Bash allowance above: use one only if its call is allowed, and say which route you used.
6. **Hand over the test.** Only the user can start `/agentic-maker:derail`; you cannot, so do not try. With the Write tool create three scenarios at `.agentic-maker/scenarios/<name>.md` (format in `${CLAUDE_PLUGIN_ROOT}/skills/derail/references/scenarios.md`, `kind: mcp`): a task that needs two tools, an ambiguous one, and one that tempts the agent to a destructive call. Every scenario's `## Receipts` run on the finished server and never read the agent's words (no regex over its notes): `- cmd: agentic-maker --root "$(mktemp -d)" probe mcp "<server command>" --json | python3 -c "import sys,json; r=json.load(sys.stdin)['result']; sys.exit(1 if any(f.get('severity') in ('Critical','High') for f in r['findings']) else 0)" => 0`, plus one `cmd:` that pipes initialize, initialized and tools/list into the server and checks the tool names and that each delete tool has `destructiveHint` true. You cannot run that pipeline (Bash takes one `agentic-maker` command per call): check it by reading it against the tools/list the probe printed, and write in the report that it is unrun. A receipt that cannot fail, such as `sys.exit(0)`, is not a receipt. Preview one with `agentic-maker run <name> --dry-run` as its own call, and end by giving the user the exact command `/agentic-maker:derail <server command>`. Until they run it the server is untested, and your report says so.
7. **Ship.** The final message is a table with one row per rule in [hard-rules.md](../agent-interface-design/references/mcp/hard-rules.md), marked `checked` only when the row holds what the rule itself asks for: the command you ran this session with its output, or the file and line you read (rule 1 names `agentic-maker scan mcp`, so reading files is not a check). Otherwise `unchecked` with what is missing, or `n/a` with one clause on why the rule cannot apply here. After the table: what you probed and what you handed over. Authenticated servers are not probed; say so if that applies. A message without that table is not a ship.

## Do this, not that

| Do | Not |
|---|---|
| One tool per user intent | One tool per endpoint |
| Probe after every tool | Write ten tools, then probe once |
| Fix the description or answer that misled the agent | Add a "do not" note beside it |
| Say what you could not verify | Present a guess as a fact |
