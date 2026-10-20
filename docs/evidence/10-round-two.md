# Evidence, round two (0.2.0)

Claude Code 2.1.304, herdr 0.9.5, macOS, 2026-10-21. Everything below was run by the author; numbers are copied from the output. Scratch work lives outside the repository (`/tmp/qc2`), run records are not committed.

## 1. Corrections to round one

### 1.1 Does the user's `CLAUDE.md` reach a worker or the reader?

Counting saved transcripts for the injected marker "Contents of `<home>/.claude/CLAUDE.md`":

```
restricted workers (am-ws-*): 0 of 38 carry the user's CLAUDE.md
in-session trace-reader subagents: 11 of 26 carry it
positive control (the interactive orchestrator transcript): 23 lines match
```

Workers are clean; the in-session reader is not. Recorded as E17 in `docs/what-is-true.md`.

### 1.2 The TypeScript and Rust samples, compiled

Round one wrote that `tsc` and `rustfmt` were not installed and left both sets "UNVERIFIED beyond a read". The statement was literally true and the conclusion was avoidable: `tsc` is one `npm install` away and `rustc`/`cargo` were present (the `rustfmt` shim exists but its component is missing: `error: 'rustfmt' is not installed for the toolchain`).

**TypeScript, 98 blocks.** `typescript` 7.0.2, `@modelcontextprotocol/sdk` 1.32.1, `zod` 4, `@types/node`, `express`, `hono`, `agents`, `@cloudflare/workers-oauth-provider` 1.2.3, `@cloudflare/workers-types`, `mcp-handler` 2.3.0, `module: nodenext`.

| | Before the edits | After |
|---|---|---|
| Blocks with a syntax error | 4 (`auth-identity.md:11`, `schema-design-portability.md:54`, `schema-design-shapes.md:94`, `tool-descriptions.md:68`; a `...` placeholder, a top-level `return`, bare object literals) | **0** |
| Every `@modelcontextprotocol/sdk` import resolves | yes | yes |

Defects found by the type check, not by reading, all fixed in the pages:

| Page | Defect |
|---|---|
| `frameworks/mcp-ts/deployment-platforms.md`, `fresh/mcp-platform-vercel.md`, `fresh/mcp-platform-picker.md` | `@vercel/mcp-adapter` on npm is a stub (0.3.2, a README that says "Package has been moved"); the live package is `mcp-handler` 2.3.0, which exports `createMcpHandler` |
| `frameworks/mcp-ts/deployment-platforms.md` | `new OAuthProvider({...})` fails to type-check with `workers-oauth-provider` 1.2.3: `resourceMetadata` is required; `createMcpHandler()` needs an initializer |
| `frameworks/node/agent-integration-frameworks.md` | `z.record(z.string())` takes two arguments in Zod 4 (`z.record(z.string(), z.string())` works in 3 and 4) |
| `frameworks/mcp-ts/agentic-patterns-serf.md` | a top-level `return` in the usage line |

Still not checked: 22 third-party packages that were not installed (`openai`, `pino`, `ioredis`, `@langchain/*`, `@opentelemetry/*`, `vitest`, `@aws-sdk/client-sqs`, `@vercel/blob`, `commander`, ...): those samples are checked for syntax only. Three blocks fail for reasons that belong to the compile setup, not to the page (`Ajv` default import under `nodenext`, a Cloudflare `Message` type that shadows a placeholder, relative imports without a file extension).

**Rust, 6 blocks (4 pages).** `rustc` 1.98.1 parses all six. With `clap` 4, `serde`, `serde_json`, `thiserror` 2, `uuid`, `assert_cmd` and `predicates`, `cargo check --tests` exits 0 for the four pages once `frameworks/rust/examples-cli.md` carries its `use` lines (it had none; the types it uses are defined on `examples.md`, which the page already said).

### 1.3 The clean twin was not clean

Round one wrote that a full audit "finds 9 ordinary gaps" in the clean twin. No list of them exists in any commit. Round two ran the audit for real (`claude -p "/agentic-maker:audit clean-cli/clean-cli" --restricted ...` in a scratch directory, plugin loaded with `--plugin-dir`): 12 tool calls, $0.177, first Bash call `agentic-maker probe cli`, sentinel absent. Its report:

| # | Severity | Finding |
|---|---|---|
| F1 | High | an unknown flag is accepted and the command succeeds (`list --bogus --json` exits 0) |
| F2 | Medium | a missing argument is reported as not-found, exit 3 (`get --json`) |
| F3 | Medium | per-subcommand `--help` does not work (`list --help` lists items, `get --help` exits 3) |
| F4 | Medium | `get` returns less than `list` for the same item |
| F5 | Medium | error envelope has no `retryable` or `suggestion` |
| F6 | Low | minimal envelope (no `command`, no `meta.total_count`) |

So the false-positive control was producing true positives. The twin was rewritten (`fixtures/cli/clean-cli/clean-cli`): unknown options exit 2, per-command help, `get` returns `name`, errors carry `code`, `retryable` and `suggestion`, errors found while parsing are already JSON. Writing it, the probe caught one of my own bugs (`--bogus` before `--json` was not emitted as JSON). After the fix:

```
default probe:        0 findings (exit 0)
the audit's extra probes (--safe "list --bogus --json # expect-exit 2", "get --json # expect-exit 2", ... --sub list --sub get --sub delete):   0 findings (exit 0)
```

A full audit rerun on the final audit text is in the last section.

The same audit run broke the skill's own rule once: it put `delete 1 --dry-run` in `--safe`, and said so in its report ("against the spirit of the rule"). `delete` with a dry-run flag is a state-changing command whose flag the auditor cannot know is honoured; on `seeded-cli`, which has no dry-run, that command would have run the delete. The rule's text gave the prohibition without the reason; section 8 of this file records the rewrite.

## 2. Does the knowledge help? Baseline, before any steering text changed

Headless workers (`claude -p --restricted --strict-mcp-config`, model sonnet, 40 turns, $2 cap each), 3 samples per arm, a fresh copy of the fixture each time, an everyday prompt that names neither the plugin nor a skill. "With" loads this plugin (`--plugin-dir`); "without" is the same command without it. Graded afterwards by the plugin's own probes on what the worker left behind.

| Task | With the plugin | Without | Skill fired (with) | `agentic-maker probe` run by the worker |
|---|---|---|---|---|
| (a) `seeded-cli`: "agents keep tripping over it, make it work reliably" (pristine fixture: 11 findings, 4 High) | 2, 3, 2 findings (High 2, 2, 1) | 4, 5, 5 (High 1, 2, 2) | 3 of 3 | 0 of 3 |
| (b) build a small MCP server from `_mini.py`: search, read, delete notes | 0, 1, 0 | 0, 0, 0 | **0 of 3** | 0 of 3 |
| (c) clean up the 24-tool seeded MCP server (pristine: 16 findings, 2 High) | 0, 0, 0 | 1, 0, 4 | 3 of 3 | 0 of 3 |
| (b0) add a calendar-delete tool to a server that already has `delete_user` | all six runs copied the existing pattern: `destructiveHint: true`, a warning in the description | same | 0 of 3 | n/a |

What it says, plainly:
- On the CLI task the plugin arm ends with about half the findings (mean 2.3 against 4.7) and the same number of High ones. The `secret.argv` finding (a token documented on the command line) survives in all three plugin runs, because nobody ran the probe.
- On small MCP tasks Sonnet already builds a clean server without help; the grader cannot tell the arms apart, and on the plain "build an MCP server" request the skill did not fire at all.
- No worker in the plugin arm ran `agentic-maker probe` (0 of 9): the write-time loop (build, probe, fix) is not in the text they were given.
- Harness noise: 3 plugin-arm and 4 plugin-less runs hit one or two permission denials of compound commands (`cd ... && ...`, `for` loops, heredocs) that the allow-list did not match; the workers recovered, and both arms are affected alike.

The same tasks are rerun after the steering text changes (last section).
