# Output Contract Checklist

> Read when: you are about to call a CLI's output contract done, or reviewing one against the full standard.

<!-- src: audit-agentic-cli/references/output-contracts.md#Checklist -->
## Checklist

- [ ] `--json` flag outputs structured JSON to stdout
- [ ] Errors include `class`, `code`, `message`, `retryable`
- [ ] Exit codes match the taxonomy (0-8)
- [ ] Progress/logs go to stderr only
- [ ] Streaming operations use JSONL with `type` field
- [ ] Stream events include timestamps (ISO 8601 UTC)
- [ ] Pagination includes `has_more` and cursor
- [ ] `--quiet` mode outputs bare values
- [ ] Exit codes are documented in `--help`
- [ ] Long operations emit heartbeat events every 30s

Details: `envelope-and-errors.md`, `exit-codes.md`, `streams-and-jsonl.md`, `pagination.md`, `quiet-mode.md`. The short pass/fail gate before calling a CLI agent-ready is `checks.md`.
