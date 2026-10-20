# Evidence, ledger row 9: the second review (0.1.1)

Recorded 2026-10-20 on Claude Code 2.1.304 (subscription login), herdr 0.9.5, macOS. After 0.1.0 was published, the content was read again from the top by the person who wrote it, then by sub-reviewers, and every claim that could be checked was checked before it was edited. This file records what was found, what was changed and what was watched running afterwards. Live runs used a scratch project outside this repository (a copy of `fixtures/skill-project` plus the seeded CLI and MCP server); the run directories are not kept (they hold session metadata).

## 1. What was wrong in 0.1.0 (and is fixed in 0.1.1)

| Area | Finding | Fix |
|---|---|---|
| Loop | `--rounds` and `--budget-usd` were stored but never enforced | `ledger fix` counts rounds and refuses past the limit (`rounds_exhausted`); `run --session` refuses once the workers' recorded cost reaches the budget (`budget_exhausted`); both exit 5. Reader cost is not metered, and the docs say so |
| Loop | `check diff` judged against git `HEAD` (round 2 saw round 1's edits) and passed any edit that removed some line | `ledger fix` keeps a copy of the controlling file per finding; `check diff --session` judges against that copy; a rule added beside an unchanged cause is flagged whatever else was removed |
| Loop | A plugin target was used in place; a worker allowed `Write` could change the real plugin | Plugin targets are copied into the take directory, as skill targets already were |
| Loop | Workers received every `AWS_*`, `GOOGLE_*`, `ANTHROPIC_*`, `CLAUDE_CODE_*` variable, including the orchestrator's own messaging socket and token | Cloud credentials only when the matching `CLAUDE_CODE_USE_*` flag is set; the orchestrator's `CLAUDE_CODE_MESSAGING_*`, `CLAUDE_CODE_SESSION_*`, `CLAUDE_CODE_CHILD_SESSION` and `HERDR_*` never pass; `run --dry-run` lists the names that do |
| Loop | Nothing kept `.agentic-maker/runs/` (full transcripts) out of the user's git | The first state write creates `.agentic-maker/.gitignore` (`runs/`, `active/`) |
| Loop | Default worker tools are read-only, so a task that writes a file failed on permissions and the reader then blamed the skill | `run --dry-run` warns when a receipt expects a file and `tools` ∩ `allowed_tools` has no `Write`/`Edit`/`Bash`; `scenarios.md` explains the two lists |
| Loop | Ctrl-C exited 1; malformed receipts crashed with `AttributeError`; `name: 12` crashed `slug()` | Exit 130; teaching messages; names are coerced |
| Loop | A closed ledger left findings in `fixing` | `ledger close` resolves them (`fixed`, `unverified`, `abandoned`) |
| Skills | `audit` told the fork never to run the target and the workflow file told it to run steps by hand | Steps are probe flags; no "by hand" left |
| Skills | The reader never saw the 31 root-cause codes; two scorecards; `design` asked 12 questions "verbatim with AskUserQuestion" | One-line meaning of every code in `trace-reader.md`; one eight-dimension scorecard with a finding→dimension table; closed questions use AskUserQuestion, open ones are plain text |
| Skills | `cli/checks.md` rated "JSON mixed with progress on stdout" Critical, `audit/references/scoring.md` rated it High (found by the audit run in section 3) | One rubric in both |
| References | Tool-count ceiling stated three ways (20, 30, 40); description length stated two ways | One ladder: up to 20 eager tools is fine, past about 20 expose only the task's tools, about 30 warn, 40+ meta-tools, 100+ semantic search; aim at about 100 tokens per description, never above 200 |
| References | MCP security pages disagreed with the 2025-11-25 specification (client registration order, form-mode elicitation for secrets, invented auth-state signal, PRM fields, 401/403, `completions` as a client capability, sampling `toolChoice`) | Rewritten against the fetched spec pages (section 2) |
| References | CLI pages contradicted each other (continuation modes, missing-flag class, `schema_version`, terminal event names, steering block, bash comments after `\`) | One canonical choice per item, the exit-code table wins |
| References | About 210 code-sample findings in `frameworks/` from a page-by-page review | Fixed, already fixed, or rejected one by one (see section 4) |
| References | 19 `fresh/` pages had `as_of: unknown`; a $912,500 figure that is off by 100x; a third party's email address | Dated from the source's last edit or a date in the body (three marked "inferred"); `lint-refs.py` rejects `unknown`; the figure is flagged as unfounded; the address is defanged and `check.sh` scans for email addresses |
| References | 106 migration notes ("the sources disagreed ...") shipped as runtime context | The record is `docs/parity/reconciled-notes.md`; each page keeps only the rule |
| Docs | README overstated what `check.sh` guards and omitted that `probe mcp <command>` starts that command | Reworded; Safety bullet added |

## 2. Specification claims, checked against the pages

Fetched 2026-10-20 from `modelcontextprotocol.io/specification/2025-11-25/`. Each quote is verbatim.

| Claim now in the references | Page | Quote |
|---|---|---|
| Registration order: pre-registered, CIMD, DCR, ask the user | basic/authorization | "Clients supporting all options SHOULD follow the following priority order:" followed by pre-registered; "Use Client ID Metadata Documents if the Authorization Server indicates if the server supports it (via client_id_metadata_document_supported ...)"; "Use Dynamic Client Registration as a fallback if the Authorization Server supports it (via registration_endpoint ...)"; "Prompt the user to enter the client information if no other option is available" |
| Servers must not collect secrets in form mode | client/elicitation | "Servers MUST NOT use form mode elicitation to request sensitive information such as passwords, API keys, access tokens, or payment credentials"; "Servers MUST use URL mode for interactions involving such sensitive information" |
| Completion of a URL-mode flow is a notification | client/elicitation | "Servers MAY send a notifications/elicitation/complete notification when an out-of-band interaction started by URL mode elicitation is completed." |
| Sampling `toolChoice` | client/sampling | "CreateMessageRequest.params.toolChoice controls the tool use ability of the model:" with `mode` `auto`, `required`, `none`; "Clients MUST declare support for tool use via the sampling.tools capability" |
| `completions` is declared by servers | server/utilities/completion | "Servers that support completions MUST declare the completions capability:" |
| Invalid token 401, insufficient scope 403 | basic/authorization | "Invalid or expired tokens MUST receive a HTTP 401 response."; "403 Forbidden: Invalid scopes or insufficient permissions". A wrong audience is sent to OAuth 2.1 section 5.3 error handling ("If validation fails, servers MUST respond according to OAuth 2.1 Section 5.3 error handling requirements"), so the pages say that rather than naming a status the page does not name |
| PRM requires `authorization_servers` | basic/authorization | "The Protected Resource Metadata document returned by the MCP server MUST include the authorization_servers field containing at least one authorization server." (`resource` is required by RFC 9728; the pages attribute each to its source) |
| `_meta` key names | basic/index | "Implementations SHOULD use reverse DNS notation"; "Any prefix where the second label is modelcontextprotocol or mcp is reserved for MCP use." |
| Resources have no ETag | server/resources | The page never mentions ETag; it defines `lastModified` and subscriptions. The pages now say "the spec defines no ETag mechanism" |

Outside the spec, checked on the registry: `@modelcontextprotocol/cloudflare` does not exist (npm 404); `createMcpHandler` is exported by `agents/mcp` (read from the packed `agents@0.29.0` type definitions), and the page now says so.

## 3. Watched running

All rows were run by the author through herdr (an interactive Claude Code orchestrator in its own tab, started with `--plugin-dir`, answered at its dialogs, one command per step, no polling).

### 3.1 The derail loop on a skill, with the new enforcement (`skills/manifest-synth`, `--rounds 2`, budget $5)

- Baseline: takes A and B failed 4 and 3 of 11 receipts (the worker never loaded the skill: the description shared no word with "release notes").
- `ledger fix F1 F3` printed `"status": "fixing"` for both and wrote `runs/<id>/snapshots/F1/skills/manifest-synth/SKILL.md` and `.../F3/...`.
- After the edit: `check diff ... --session` printed `"verdict": "ok", "reason": "the quoted controlling text was rewritten or deleted", "added_lines": 3, "removed_lines": 3` for both.
- Rerun takes C and D: 11 of 11 receipts, 3 of 3 predicates (`tool_used`, `not_regex`, `reads_file`). The reader found no P0/P1 on take C.
- Ledger at close: `rounds_used 1`, `rounds_max 2`, `spent_usd 0.12868` of `budget_usd_total 5.0`, `status closed`, outcome `clean`.
- `.agentic-maker/.gitignore` appeared with `runs/` and `active/`.
- The dry-run preview named 23 environment variables in this session, among them `CLAUDE_CODE_MESSAGING_SOCKET` and `CLAUDE_CODE_MESSAGING_TOKEN`: the orchestrator's own messaging credentials were reaching workers. This was found by reading the preview and fixed in `runner.py`; after the fix the preview lists 18 names, none of them `CLAUDE_CODE_MESSAGING_*`, `CLAUDE_CODE_SESSION_*` or `HERDR_*`, and a worker run still completed.

### 3.2 Limits, on a copy of that project

```
$ agentic-maker ledger init --session evid-1 --target skills/manifest-synth --rounds 1 --budget-usd 0.05 ...
$ agentic-maker ledger fix F1 --session evid-1 ...      -> "status": "fixing"
$ agentic-maker ledger fix F3 --session evid-1 ...
error [conflict/rounds_exhausted]: round limit reached: 1 of 1 fix rounds used      (exit 5)

$ agentic-maker ledger init --session evid-2 ... --budget-usd 0.001
$ agentic-maker run release-notes --session evid-2      -> completed, cost_usd 0.028547
$ agentic-maker run release-notes --session evid-2
error [conflict/budget_exhausted]: the ledger's budget is spent: $0.028547 of $0.001  (exit 5)
```

### 3.3 `check diff` against the snapshot

With the pre-fix skill restored and a snapshot kept, one edit added "Always read the commit list first; you must never skip the grouping step." beside the unchanged description and deleted an unrelated line:

```
error [validation/patch_by_rule]: the controlling text is unchanged and the edit adds imperative text (1 line(s)): the agent will still read the misleading text first   (exit 6)
```

Rewriting the description itself, in the same file, printed `"verdict": "ok", "reason": "the quoted controlling text was rewritten or deleted"`. In 0.1.0 the first edit would have passed, because it removed a line.

### 3.4 The derail loop on a CLI (`/agentic-maker:derail cli/seeded-cli --rounds 1`, budget $3)

- Take 01: receipts 1 of 3 (no `report.json`). The reader's finding was root cause O6 (the harness, not the target): the worker chained `echo "exit $?"` onto its `seeded-cli` calls, the allow-list covered only `seeded-cli`, Bash was denied for the whole line and the worker stopped. The orchestrator did not touch the CLI; it added `Bash(echo *)` to the scenario's `allowed_tools`.
- Takes 02 and 03: 3 of 3 receipts, findings verified 4 of 4 and 1 of 1 (0 rejected); `/tmp/seeded-cli-delete-ran` absent after every take.
- Three real target defects (the colour banner on stdout in `list --json`, a plain-text error on stdout from `get 7 --json`, undocumented `get` output) were reported as open; the orchestrator left them alone because the fixture's defects are planted.
- Workers cost about $0.07 in all.

### 3.5 The derail loop on an MCP server (`/agentic-maker:derail mcp/seeded-server.py --rounds 1`, budget $2)

- Take 01: 10 tool calls, 6 errors. The server listed `fetch_user` and `Get-User Info` with no handler, so every call came back `Unknown tool`; a missing user came back with `isError: false`.
- Fix: the two dead tool entries were removed, `get_user` returns `isError: true` with the id. `check diff` returned `ok: true` for both findings.
- Takes 02 and 03: 3 of 3 receipts, 4 tool calls and 1 error (the intended not-found). F1's `not_regex` predicate passed; F2 (the wording of the "Unknown tool" message) was not exercised and is reported as unverified.
- The reader's quotes carried the `trace.md` label ("Error: ") and had to be corrected by hand before `check findings` passed. `trace-reader.md` now says to quote after the label.
- About $0.10 in all.

### 3.6 `audit` of a CLI, in a forked skill

- `/agentic-maker:audit cli/seeded-cli`: 11 findings (4 High, 6 Medium, 1 Low), overall 70, 5 of 8 dimensions measured; `/tmp/seeded-cli-delete-ran` absent; the main session's summary of the fork's report shows probe-based evidence and no instruction to run a step by hand (the fork's full text was not kept). The fixture has 11 planted defects.
- It found that two reference files rated the same defect differently (section 1), which is fixed.
- After the fork returned, the main session spot-checked three claims by running the target itself. The audit's report spec now ends with one line saying the probe output is the evidence and the target is not to be run again by hand. The skill's `allowed-tools` pre-approves; it does not restrict, and the README says "instructed", not "sandboxed".
- Clean twin (`cli/clean-cli`): see the last line of this section.

### 3.6b The whole ledger once more, on the final text

After the last edits to the skills and the CLI, a fresh orchestrator ran `/agentic-maker:derail skills/manifest-synth --rounds 1` on a copy with the original broken skill (budget $4):

- `ledger init ... --budget-usd 4 --rounds 1` was issued with `--rounds` on the first try (before the skill passed it, the orchestrator had to rerun `ledger init --force`).
- Baseline takes 1 and 2: 3 and 4 of 11 receipts failed; neither worker called `Skill`. The reader returned 7 findings for take 1; `check findings` verified 3 and rejected 4 (the 4 had empty `trace_refs`); the orchestrator sent them back, the second file verified.
- One fix round; `check diff --session` ran for every finding; the description was rewritten and the format rules moved into `SKILL.md`.
- Reruns, takes 3 and 4: `Skill` called, 11 of 11 receipts each. One regex predicate (anchored with `^` and `$`) could not match a JSON line and the orchestrator judged it by hand; the reader now has a line against anchoring.
- Ledger at close: `rounds_used 1`, `rounds_max 1`, `spent_usd 0.144436` of `4.0`, `closed`, outcome `clean`, findings `fixed` (this is the `ledger close` change at work).
- `/agentic-maker:audit cli/seeded-cli` again: 12 findings (the first run had 11; the audit chooses its own extra probe commands), sentinel `/tmp/seeded-cli-delete-ran` absent, the summary says it cites probe output and ran nothing itself.

A Codex review of the branch against `main` (258 files) returned one finding: `ledger close --outcome open` marked unresolved findings `fixed`. Fixed (`open` stays `open`; the four outcomes were rerun: `fixed`, `unverified`, `open`, `abandoned`). Codex was not run again on the fix.

### 3.7 `claude plugin eval` over `evals/` (first recorded run)

| Case | With plugin | Without | Δ | Runs | Cost |
|---|---|---|---|---|---|
| ignores-code-review | 1.00 | 1.00 | 0.00 | 6 | $0.14 |
| ignores-human-ui | 1.00 | 1.00 | 0.00 | 6 | $0.20 |
| triggers-agent-interface-design | 1.00 | 0.00 | +1.00 | 6 | $0.31 |
| triggers-derailment-method | 1.00 | 0.00 | +1.00 | 6 | $0.22 |

Mean Δ +0.50, 148 s, $0.88. The two "ignores" cases score the same with and without the plugin by design (the skill must stay quiet); the two "triggers" cases are the plugin-fired indicator.

## 4. The framework pages

Five workers (one per language folder, Sonnet, medium effort) took the 307 reviewer findings one by one: read the cited line, skip if already fixed, reject if the reviewer was wrong, otherwise make the smallest edit. Where a finding rested on an SDK detail nobody could confirm offline, the sample was rewritten to avoid the claim or marked "illustrative, confirm against your SDK version" (a handful of places). Rejections worth keeping: the Go and Node reviewers said JSON progress events on stderr break the stderr rule; they do not, `cli/streams-and-jsonl.md` defines them as the one carve-out (typed progress lines on stderr, the terminal line on stdout).

After the edits, every Python block parses (`ast.parse`, 123 blocks), every bash block passes `bash -n`, every Go block passes `gofmt -e` (42 blocks). TypeScript (98 blocks) and Rust (6 blocks) were not compiled: `tsc` and `rustfmt` are not installed here. They are UNVERIFIED beyond a read.

## 5. Not done, or not proven

- The `audit` skill's tool restriction is an instruction; see the README.
- Four times an `agentic-maker` command that the skill pre-approves (`check nice`, `check findings`, `check predicate`, `check receipts`) still asked for approval in a manual-permission session. A single "yes" let it through each time and nothing wrong ran. Three of the four were issued in the same assistant message as another tool call (the transcripts show it); the fourth was alone. In the last run a message with four `agentic-maker check` calls side by side asked for each of them in turn (two asked before the pattern was allowed for that scratch session), which supports the parallel-call explanation without proving it. The same commands ran without a prompt under `claude -p --permission-mode dontAsk` with the same allow rule. `derail` now asks for one Bash call per message; whether that removes the prompts was not measured. It costs a keystroke, not correctness.
- The `design` interview was not run end to end (it needs a person).
- Codex and agy workers, authenticated MCP servers, Windows: as before.
