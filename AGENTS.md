# Maintainer notes (plugin-agentic-maker)

Claude Code plugin `agentic-maker` (marketplace `plugin-agentic-maker`). Python 3.9+ standard library only; no runtime dependencies.

## Layout
- `bin/agentic-maker` -> `lib/agentic_maker/`: the CLI. Skills and agents call it; they never re-derive what it computes. `cli.py` dispatches; one module per job (`runner`, `trace`, `check`, `ledger`, `probe_cli`, `probe_mcp`, `detect`, `evalemit`, `doctor`).
- `skills/derail` (user-started, Stop gate in its frontmatter), `skills/audit` (user-started, `context: fork`), `skills/design` (user-started), `skills/agent-interface-design` and `skills/derailment-method` (model-invocable, narrow). `agents/trace-reader.md` is read-only on purpose (`Read, Grep, Glob`) and carries `omitClaudeMd: true`. `hooks/hooks.json` has the one plugin-level hook: `SubagentStop`, matcher `agentic-maker:trace-reader`, which runs `agentic-maker ledger reader-done` (a skill-frontmatter `SubagentStop` never fires, `docs/what-is-true.md` E19).
- `skills/agent-interface-design/references/`: the knowledge, one decision per file (at most 8 KB). `cli/ mcp/ skill/ decisions/ frameworks/ fresh/`. `index-*.md` and the two blocks between the `build-index:` markers in `agent-interface-design/SKILL.md` (which index lists each stack, and every index) are generated: `python3 scripts/build-index.py`.
- `data/surfaces.tsv`: detection rules. A new ecosystem is a row.
- `fixtures/`: planted-defect CLI, MCP server and skill, each with a clean twin or a recorded trace. `evals/`: trigger and negative cases for `claude plugin eval`.
- `docs/design/`: the plan this was built from (a record, not a spec). `docs/what-is-true.md`: what was checked against the real harness. `docs/evidence/`: one file per capability. `docs/parity/`: the mechanical ledger against the three source skills.

## Rules for changes
1. Run `scripts/check.sh` before every commit. It compiles the package with both `/usr/bin/python3` (3.9 on macOS) and the `python3` on PATH; to run the rest of it on 3.9, put that interpreter first on PATH. `--strict-parity` is the gate when the source clone is present (`AM_SRC=<dir with the three skills>`).
2. Bump the version in `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` (both fields) **and** `lib/agentic_maker/__init__.py` together with any shipped change; `scripts/check.sh` fails when the three differ. No path fields in `plugin.json`.
3. Every injected command in a skill ends in `|| true` (a failing one aborts the invocation silently). Hook commands use `"${CLAUDE_PLUGIN_ROOT}/bin/agentic-maker"` with the path quoted: `bin/` is on the Bash tool's PATH, not on a hook's. A hook handler never raises and never blocks except to send a reply back once.
4. A claim about Claude Code or herdr behaviour goes in `docs/what-is-true.md` with what was run. A time-sensitive fact goes in `references/.../fresh/` with `as_of`.
5. Reference files: `# Title`, then `> Read when: ...`, one decision, at most 8 KB; migrated sections carry a `<!-- src: ... -->` marker (the parity checker reads them). A path in backticks inside `skills/` (`dir/file.md`) must resolve from the file's folder, the skill, its `references/` or the knowledge base `references/`; `scripts/check-links.py` checks it. A pointer into another skill is written `skills/<skill>/references/<file>.md` (relative to the plugin root), and the plugin's CLI is written `agentic-maker`, never `bin/agentic-maker`. A page states a rule, not where the rule came from: history belongs in `docs/parity/`.
6. Fixtures are re-recorded only after reading the diff. Fixture CLIs that can do damage create a sentinel; `check.sh` fails if a probe ever creates it.
7. Never commit a token, a run directory (`.agentic-maker/runs/`), a trace of a real session, a personal path or an email. Commit under the GitHub noreply identity.
8. Probes and `check.sh` never write into the repository: a probe saves its reply under the project root's `.agentic-maker/runs/`, so the gate passes `--root` a scratch directory.
9. `agy` is never launched by anything here: a launch can have effects the plugin cannot see (which account, which quota). Analyse a session the user already ran, with `--runner existing`.
