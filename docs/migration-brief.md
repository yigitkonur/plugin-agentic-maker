# Migration brief — moving the three source skills' reference content into this plugin

This is the contract for anyone (human or subagent) who moves content from `audit-agentic-cli`, `audit-agentic-mcp` and `audit-skill-by-derailment` into this plugin. The sources are read from a scratch clone; nothing is edited there. Read the whole of each source file you migrate, in full, before writing.

## What you are doing

The sources are a body of knowledge about making tools that agents use well. The knowledge is the valuable part; the old packaging (three skills, sidecar `.sh.md` docs, one 80 KB file per topic) is not. You re-cut the knowledge into small files that an agent can load one at a time, and you repair the known defects while doing it. You are **not** summarizing: every rule, threshold, number, identifier, table row and worked example must survive, in tighter prose if you like.

## Where files go

Everything lands under `skills/agent-interface-design/references/` unless a batch says otherwise:

```
cli/          contract and behaviour of a CLI an agent drives
mcp/          design, budget, ops, protocol and security of an MCP server
decisions/    decision trees and the surface-choice rules
frameworks/   per-language/stack code (Go/Cobra, Python/Click, Node, Rust/clap, Bash, TS/Python MCP SDKs)
fresh/        time-sensitive facts (versions, prices, clients, models, registries, CVEs, benchmarks)
```

Language-specific code goes **only** in `frameworks/`. A core file shows at most one neutral example (shell plus JSON).

## File rules (checked by a script; a violation is a failed batch)

1. **Size:** at most 8 KB per file (hard cap 10 KB). Split by decision, not by length.
2. **One decision or topic per file.** Name it for the question it answers (`exit-codes.md`, `retry-and-idempotency.md`).
3. **Shape:** line 1 `# Title`; line 3 `> Read when: <one line, the situation in which an agent should open this file>`; then `##` sections. Stable headings: do not number them.
4. **No front matter**, except in `fresh/`, which starts with:
   ```
   ---
   as_of: <date the SOURCE says, or "unknown">
   verify_before_citing: true
   ---
   ```
5. **Voice:** second person or imperative, about "the agent" and "the CLI/server/skill". No author-local references (a named companion skill, a personal repo, a private path). If the source points to one, keep the *idea* and drop the name, and record the drop (below).
6. **No domain leakage:** no media-file types, no result-delimiter strings, no tool names from the video skill.
7. **Time-sensitive claims** (model names and limits, client support matrices, vendor behaviour, prices, CVE numbers, registry URLs, "as of" statements, benchmark numbers) never appear in a core file. They go to `fresh/` with their original date, and the core file links to them in one line.

## Provenance markers (the parity checker reads these)

Directly above every section that carries source content, put one marker line:

```
<!-- src: audit-agentic-cli/references/output-contracts.md#3. Exit Code Taxonomy -->
```

- The key is `<skill>/<path under that skill>#<heading text exactly as written in the source, without the # characters>`.
- A heading that repeats inside one source file takes a `~2`, `~3` suffix for its second and third occurrence (`#Examples~2`).
- One destination section may carry several sources: `<!-- src: a.md#X | a.md#Y -->`.
- Every H1, H2 and H3 of every source file that is not inside a code fence must be claimed by exactly one marker somewhere in the new corpus, **or** be listed in `docs/parity/dropped.tsv` as `source key<TAB>reason` (reason at least ten characters, saying why nothing of it is needed).
- Headings of level 4 and deeper are not tracked; their content travels with the parent section.
- Run `python3 scripts/parity.py check --no-write` yourself. It prints the unmapped headings. Zero unmapped is the target; a dangling marker (a key that does not exist) is an error.

## Content you must keep intact

Numbers and thresholds (400/2000/4000/20, 6 required params, 30 s heartbeat, 100 tokens, and so on); every row of every table; named identifiers in backticks; every checklist item; every decision-tree branch (keep trees as indented text or a table); worked examples (in `frameworks/` when language-specific).

## The known defects and the one answer for each

Where two source files disagree, **use the answer below, and say so in one line** at the point of use (`> Reconciled: the sources gave X and Y; this file uses Z.`). Do not silently pick a side where the table below is silent: write both claims, mark it `> Unresolved:`, and list it in your report.

| Defect | The answer |
|---|---|
| Exit-code taxonomy 0–7 vs 0–8; label of 1 | One table: **0** success · **1** crash (unexpected/internal) · **2** usage · **3** not_found · **4** auth · **5** conflict · **6** validation · **7** transient (retryable: rate_limit, timeout, network, dependency_failed) · **8** partial. |
| Batch "partial" reported as exit 3 | Partial is **8**, never 3. |
| Error class enums differ (`auth` vs `authentication`; `usage`/`transient` missing) | Classes: `usage, not_found, auth, conflict, validation, rate_limit, timeout, network, dependency_failed, internal, partial_success`. `transient` is the exit-7 group name, not a class. The class is `auth`. |
| Error JSON on stdout in one file, stderr in another | In `--json` mode the envelope (success **and** failure) is written once to **stdout**; stderr carries human diagnostics only and never JSON. A CLI that varies by case, or that documents neither, is the finding. |
| Progress/JSONL on stdout vs stderr | A command that streams *results* emits typed JSONL on stdout (last line `type: summary` or `result`). Progress that is not a result goes to stderr. Never mix them on one stream. |
| Credential precedence differs | Flag (never a secret value on argv: use `--token-file` or stdin) → environment variable → project config → user config → OS credential store. |
| Non-interactive confirmation: exit 2 vs error vs false/exit 1 | Without a TTY and without `--yes`/`--force`, a confirming command **fails with exit 2** naming the flag. It never returns false silently and never hangs. |
| `--stop-on-error` default contradiction | State it once: read-only and idempotent batches default to *continue and report partial (exit 8)*; destructive batches default to *stop at the first error*. `--stop-on-error` / `--continue-on-error` override either. |
| Pagination field names differ | `result.items`, `result.next_cursor`, `result.has_more`, optional `result.total`. |
| Test script `((PASS++))` miscounts the first pass | Use `PASS=$((PASS + 1))`. |
| Go constants `ExitAuthDenied` vs `ExitAuth` | `ExitAuth`. |
| Audit scoring rubric undefined; a "18/25" that is not a multiple of 5 | Do not invent a rubric in a reference file. Keep the illustrative audits, mark each *illustrative; not re-verified against current versions*, and leave the rubric to `skills/audit/references/scoring.md`. |
| gh/kubectl/aws audit results | Illustrative only (see above); the numbers move to `cli/case-studies.md` with that label. |
| Two client-compatibility matrices disagree | Both go into `fresh/client-compatibility.md` with their dates and a `## Conflicts` section listing each disagreement and both claims. No silent merge. |
| Tool-description length guidance conflicts | Target at most about 100 tokens, never above 200; the first five words are Verb + Resource; put long examples in the parameter descriptions of the input schema. |
| Tool-count ceilings 10/20/30/40 | Diagnostic cues, not verdicts: up to 20 active tools is the default comfortable range, about 30 is a warning, 40 or more needs progressive discovery. Per-model caps live in `fresh/`. |
| `oneOf`/`anyOf` and enum-size thresholds (10 vs 20) | Avoid `oneOf`/`anyOf` at the top of an input schema; inline enums up to 10 values; above that describe the values and validate on the server. Keep the 20 claim in `fresh/model-behavior.md`, marked as a model-specific report. |
| DCR / CIMD stance varies | Prefer Client ID Metadata Documents where the client supports them; Dynamic Client Registration remains for clients without them; never assume either, detect it from the authorization-server metadata. |
| Arithmetic and cross-reference errors (cache TTL "8×", Cloud Run "double", a wrong pattern pointer, a dangling "polling-tool pattern") | Fix the arithmetic from the numbers given in the same file (TTL ratio 4×, Cloud Run 4.5×); repair or remove the dangling pointer and say so in the report. |
| Dated claims already past (Asana V1 sunset, "refreshed April 2026") | Move to `fresh/` with their date and the line "verify before citing". |
| Steering through tool output vs tool output as untrusted input | State the tension once, in `decisions/steering-contract.md`: steering text in tool output is the strongest lever and the same channel is the attack surface; bridge it with namespaced guidance plus an `allowed_next_tools` list. Other files link to it. |
| "Steps for `linear-cli`, `run-railway`, `build-mcp-*`, `test-by-mcpc-cli`" companion skills | Keep the idea (a companion may exist), drop the names from core files; list them once in `decisions/companion-routing.md` as optional, "if installed". |

## What to report when you finish

Raw output only, no prose summary: the list of files you wrote with their byte sizes, the output of `python3 scripts/parity.py check --no-write` restricted to your source files, every `> Unresolved:` and `> Reconciled:` line you wrote, and every heading you proposed to drop (as `dropped.tsv` rows, not applied).
