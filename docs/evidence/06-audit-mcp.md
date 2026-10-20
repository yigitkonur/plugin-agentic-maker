# Evidence, ledger row 6: auditing an MCP server

Recorded 2026-10-20. Target: `fixtures/mcp/seeded-server.py`, a stdlib stdio server with 24 tools and planted defects, and `fixtures/mcp/clean-server.py`. `probe mcp` talks to the server as a client does (`initialize`, `tools/list`, `tools/call` for the read-only tools named with `--call`).

## Budget numbers against a hand count

```
$ printf '{"jsonrpc":"2.0","id":2,"method":"tools/list"}\n' | python3 fixtures/mcp/seeded-server.py | tail -n +2 \
    | jq -c '.result.tools|[(map(tojson|length)|add), length]'
[5724,24]
$ agentic-maker probe mcp "python3 fixtures/mcp/seeded-server.py" --json | jq -c '[.result.budget.definition_chars, .result.budget.tools]'
[5724,24]
```
5724 characters over 24 tools, about 1431 tokens at chars/4. The old `measure-context-budget.sh` run on the same directory reported "Tool registration candidates: 15", "Combined heuristic budget: ~459 tok" and "No threshold flags".

## Planted defects against what each tool found

| Planted defect | `probe mcp` | old `audit-mcp-server.sh` / `measure-context-budget.sh` |
|---|---|---|
| a banner printed on stdout before the protocol | **Critical** `stdio.pollution`, first line quoted | not detectable by reading source in general |
| `get_user` returns "Error: user not found" with `isError: false` (via `--call`) | High `response.error_as_success` | no |
| `export_all` returns about 50 KB (via `--call`) | High `response.big`, chars and tokens | no |
| `delete_account` without `destructiveHint` | High `destructive.unmarked` | no |
| `ping_thing` with no description | High `description.missing` | no |
| `get_user` / `fetch_user` identical descriptions; 15 `list_report_N` tools alike | Medium, one clustered finding per group (M7) | no |
| `Get-User Info` as a tool name; a 700-character description | Medium `name.unsafe`; Low over the length cue | no |
| `create_ticket`: 8 required parameters, 4 levels deep | Medium wide, Medium deep | no |
| `search` with a top-level `oneOf` | Medium | no |
| a 14-value enum | Low | no |
| 24 tools | Low past the comfortable range (a cue, not a verdict) | flags only above 20 candidates by regex (it found 15) |

18 findings today: 1 Critical, 4 High, 7 Medium, 6 Low (17 when this was first recorded; a later check, a description under 25 characters, adds one clustered Medium). Every planted defect has a finding. **Clean twin: 0 findings, exit 0.**

The HTTP transport was exercised against the same fixtures in `--http` mode: `probe mcp http://127.0.0.1:18765/mcp` reports `streamable-http` and the same numbers; an unreachable port exits 7 (`network/connect_failed`).

## Limits

- Fixtures are small and written alongside the probe. They show the checks work and the numbers are right, not that the thresholds are right for every server; the thresholds are cues (the references say so).
- Only unauthenticated servers are measured. OAuth servers are reported as not measured, with a route to `mcpc` / MCP Inspector.
- The token estimate is chars/4, labelled as such.

## The skill, run for real

`/agentic-maker:audit "python3 .../seeded-server.py"` in a fresh session with only the plugin loaded: two `agentic-maker` calls (`probe mcp`, `scan mcp`), the MCP hard rules and the scoring rubric read from the references, and a report with a scorecard, the probe's findings of that day (before the thin-description check) plus source-level findings, what was executed, what was not run (`tools/call` for anything), and assumptions. Cost about $0.075, no permission denials.

Friction found by running it, fixed afterwards:

- `scan mcp <file>` failed (it wanted a directory): it now accepts a file.
- The agent said the probe output "was truncated in the middle (about 2.3k characters)" and filled the gap from source. The envelope was 12 KB, mostly a per-tool table; a tool for agents must not exceed what an agent reads. The per-tool rows are now omitted by default (`--full` brings them back; the five largest definitions are always in `budget.largest`): 12.3 KB -> 8.0 KB, with the audit skill told to read the whole reply.
