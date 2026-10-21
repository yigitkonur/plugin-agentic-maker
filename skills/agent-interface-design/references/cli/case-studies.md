# CLI Audit Case Studies

> Read when: you want a worked example of how a widely used CLI scores against the agent-readiness checks, or the design patterns reference CLIs are worth copying for.

> Illustrative; not re-verified against current versions. The command results below are from the source's audit and describe the CLIs as they were then. The source also scored each CLI on a /133 point scale; that scale is dropped here because its own weights cannot reproduce its subtotals (it gave kubectl 18/25 from checks worth +5 each) and this plugin scores differently (`skills/audit/references/scoring.md`). Report shape for a real audit: `skills/audit/references/report.md`.

<!-- src: audit-agentic-cli/references/examples.md#Local CLI Exemplars -->
## Patterns worth copying

Use reference CLIs as design anchors before reaching for generic examples. Two patterns from the source's local exemplars (the companion skills themselves are listed, if installed, in `../decisions/companion-routing.md`):

| Exemplar pattern | Worth copying |
|---|---|
| A tracker CLI | JSON on every command, `--dry-run` before bulk writes, `--id-only` for chaining, `--no-pager` discipline, an explicit exit-code contract, and bulk mutation gates. |
| A deploy-platform CLI | An installed-help snapshot as local truth, the distinction between upstream commands and locally installed ones, refresh scripts, and version-drift routing. |

<!-- src: audit-agentic-cli/references/examples.md#11. Real-World CLI Audit: GitHub CLI (gh) | audit-agentic-cli/references/examples.md#Critical Checks -->
## GitHub CLI (`gh`)

Critical checks:

| # | Check | Test Command | Result |
|---|-------|--------------|--------|
| C1 | JSON output | `gh repo view --json name,description \| jq .` | PASS - clean JSON |
| C2 | stdout/stderr separated | `gh repo view --json name > out.txt 2> err.txt` | PASS - out.txt is pure JSON |
| C3 | Semantic exit codes | `gh repo view nonexistent/repo; echo $?` | PARTIAL - returns 1 for all errors |
| C4 | Non-interactive | `gh pr create < /dev/null` | PASS - errors with usage message |
| C5 | Structured errors | `gh api /nonexistent --jq '.message'` | PASS - returns `{"message":"Not Found"}` |

<!-- src: audit-agentic-cli/references/examples.md#Important Checks (each +5) -->
### Important checks

- PASS: consistent field types (snake_case JSON)
- PASS: `--dry-run` in `gh pr merge --dry-run`
- PASS: good `--help` with examples
- FAIL: no explicit conflict handling (exit 1 for exists)
- PASS: noun-verb grammar (`gh repo create`, `gh pr list`)

<!-- src: audit-agentic-cli/references/examples.md#Nice-to-Have Checks (each +2) -->
### Nice-to-have checks

- FAIL: no JSONL streaming for `gh run watch`
- PASS: `--jq` for quiet/filtered output
- FAIL: no `schema_version` in outputs
- PASS: `gh run watch` for async jobs

<!-- src: audit-agentic-cli/references/examples.md#Final Score -->
### Final score

The source's point total and grade are dropped (see the note at the top); the fixes and strengths below are what carried the value.

<!-- src: audit-agentic-cli/references/examples.md#Key Fixes Needed -->
### Key fixes needed

1. Exit codes: currently 1 for all errors. Differentiate 3 for "not found", 4 for auth failures, 5 for conflicts.
2. Structured errors: API errors are structured, but CLI errors are just stderr text.

<!-- src: audit-agentic-cli/references/examples.md#What gh Does Right -->
### What `gh` does right

1. Universal `--json` flag across all commands.
2. `--jq` for in-line filtering (reduces agent parsing).
3. Clean separation of stdout (data) and stderr (messages).
4. `--template` for custom output formatting.
5. Good example-driven `--help` text.

<!-- src: audit-agentic-cli/references/examples.md#12. Real-World CLI Audit: kubectl | audit-agentic-cli/references/examples.md#Critical Checks~2 | audit-agentic-cli/references/examples.md#Summary -->
## `kubectl`

| # | Check | Test Command | Result |
|---|-------|--------------|--------|
| C1 | JSON output | `kubectl get pods -o json \| jq .kind` | PASS |
| C2 | stdout/stderr | `kubectl get pods -o json 2>&1 \| head` | PASS |
| C3 | Exit codes | `kubectl get nonexistent; echo $?` | PARTIAL - 1 for all |
| C4 | Non-interactive | `kubectl delete pod x < /dev/null` | PASS - requires `--force` |
| C5 | Structured errors | Error messages are plain text | FAIL |

- Strengths: multiple output formats (`-o json`, `-o yaml`, `-o jsonpath`), `--dry-run=client`, excellent `--field-selector` filtering.
- Weaknesses: errors are unstructured text, exit codes are binary (0 or 1), no in-line jq filtering.

<!-- src: audit-agentic-cli/references/examples.md#13. Real-World CLI Audit: AWS CLI | audit-agentic-cli/references/examples.md#Critical Checks~3 | audit-agentic-cli/references/examples.md#Summary~2 -->
## AWS CLI v2

| # | Check | Test Command | Result |
|---|-------|--------------|--------|
| C1 | JSON output | `aws s3api list-buckets --output json` | PASS - default is JSON |
| C2 | stdout/stderr | `aws s3 ls 2>&1 \| grep -v "^{"` | PASS |
| C3 | Exit codes | `aws s3 ls s3://nonexistent; echo $?` | PARTIAL - 1 or 255 |
| C4 | Non-interactive | All commands non-interactive by default | PASS |
| C5 | Structured errors | `aws s3 ls s3://x 2>&1` | PASS - JSON error objects |

- Strengths: JSON output by default, `--query` for JMESPath filtering, structured error responses, `--dry-run` for EC2, excellent pagination with `--max-items`.
- Weaknesses: exit codes not semantic (255 for API errors), no streaming JSONL for long operations, waiter output not machine-parseable.

<!-- src: audit-agentic-cli/references/examples.md#Key Takeaways from Real-World Audits -->
## Key takeaways

| CLI | Best Feature | Biggest Gap |
|-----|--------------|-------------|
| gh | `--jq` inline filtering | Exit codes |
| kubectl | Multiple output formats | Unstructured errors |
| aws | JSON default + `--query` | Exit code semantics |

Common patterns in production CLIs:

- All support JSON output (a table is usually the default for humans).
- Exit codes are universally weak (0/1 binary).
- Inline filtering (`--jq`, `--query`, `-o jsonpath`) is the differentiator.
- Structured errors are inconsistent even in "agent-ready" CLIs.
