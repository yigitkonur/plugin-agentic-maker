# The agent-interface contract: eight questions

> Read when: you design, review or audit anything an agent will call or read - a CLI, a script, an MCP server or tool, a skill - and need the questions that apply to all of them.

A surface is "agent-facing" when a model, not a person, is its user: it reads the text, picks the call, parses the answer and decides what to do next. The CLI checklist (`cli/checks.md`) and the MCP rulebook (`mcp/hard-rules.md`) are two instances of the same eight questions. Answer each one for the surface in front of you, cold (as an agent that has only the surface itself would).

| # | Question | If the answer is no, the agent... |
|---|---|---|
| 1 | **Intent.** Is it built around what the agent is trying to do, not around endpoints or internals? | picks among look-alike calls, chains five where one would do |
| 2 | **Contract.** Are inputs, outputs and errors machine-checkable and consistent? | scrapes prose, misreads success as failure |
| 3 | **Discovery.** Can it learn the surface from the surface itself, with examples? | guesses flags and shapes, or never chooses the target (T1) |
| 4 | **Steering.** Does each answer say what to do next, within bounds? | stalls, or invents the next step |
| 5 | **Safety.** Are destructive actions explicit, secrets off the command line, untrusted text marked? | hangs on a prompt, deletes without a preview, leaks a token |
| 6 | **Budget.** Is the cost in context proportionate (definitions, responses)? | loses the task under 40 tool definitions or a 50 KB reply |
| 7 | **Recovery.** Do errors teach: which field, what was expected, what to call, how often to retry? | repeats the same failing call (C5) |
| 8 | **Verification.** Can it be exercised live, non-interactively, without ever hanging? | cannot be tested, so is never tested |

## How each question looks per surface

| # | CLI / script | MCP server / tool | Skill |
|---|---|---|---|
| 1 | commands named for tasks (`deploy`, not `post-v2-resource`); `--help` per task | intent-based tools, not one tool per endpoint; workflow tools for multi-step jobs | one job per skill; the description states the job in a user's words |
| 2 | stdout is data, stderr is the operator, the exit code is the class, and all three agree; one JSON envelope; exit codes 0-8 | `structuredContent` + text; `isError` for tool failures, protocol errors only for protocol; flat typed schemas (at most about 6 required parameters) | the steps name exact files, commands and outputs; no step that only says "handle" |
| 3 | `--help` with examples and exit codes; `--version`; stable names | Verb + Resource in the first five words of each description; `instructions`; enums inline | `description` (in the words a user says), a routing table "read X when Y", no orphaned reference |
| 4 | `next_actions` / suggestions in the envelope; continuation modes (`none`, `suggest`, `prefetch`, `closed-loop`; `cli/continuation-modes.md`) | guidance in tool output with `allowed_next_tools`; namespaced; bounded | phase gates with a checkable exit; "only run this if ..." conditions |
| 5 | `--dry-run`, `--yes`/`--force`, fails with exit 2 naming the flag when it cannot ask; secrets via file/stdin/env, never argv | annotations (`readOnlyHint`, `destructiveHint`); confirmation scaled to stakes; OBO tokens, no passthrough; treat tool output as untrusted | destructive steps staged (shadow, flip, neutralize); no secrets in text |
| 6 | concise default output, `--fields`, pagination, caps | at most about 20 active tools; concise/detailed modes; truncation signals; progressive discovery past that | short SKILL.md, references loaded on demand; descriptions that earn their always-on cost |
| 7 | error = class + message + `retryable` + `suggestion`; the exit code names the class | errors name the field, the expected value, a recovery call with real values; retry cap and a loop breaker | a failure path for each step that can fail |
| 8 | never prompts without a TTY; timeouts; a read-only way to probe | stdio hygiene (nothing but protocol on stdout); a way to list and call without a client | a scenario an agent can run cold and a receipt that proves the result |

## Using the contract

- **Auditing.** `/agentic-maker:audit` probes the surface at runtime where it can (the CLI is run, the server's `tools/list` is read) and walks these eight questions for the rest. Findings are written in agent terms: can the agent parse it, continue after an error, avoid side effects?
- **Designing.** Start from question 1: write the agent's task, then the smallest surface that serves it, then the answers to 2-8. `/agentic-maker:design` runs this as an interview.
- **Testing.** Questions 3, 4 and 7 are about behaviour you only see in a run: `/agentic-maker:derail` shows what an agent actually does with the text and tells you which sentence caused it.

Fix the surface before blaming the architecture: most agent failures that look like "MCP is wrong" or "the model is weak" are an unparseable stdout, an error that does not teach, or a description nobody reads. Check those first (see [checks](cli/checks.md) and [hard-rules](mcp/hard-rules.md)).

## Where to read next

| Question | CLI | MCP |
|---|---|---|
| 1 Intent | [checks](cli/checks.md) | [design-intent-based-tools](mcp/design-intent-based-tools.md) |
| 2 Contract | [envelope-and-errors](cli/envelope-and-errors.md), [exit-codes](cli/exit-codes.md), [streams-and-jsonl](cli/streams-and-jsonl.md) | [schemas-flat-and-sized](mcp/schemas-flat-and-sized.md), [responses-curated-and-semantic](mcp/responses-curated-and-semantic.md) |
| 3 Discovery | [discovery-and-help](cli/discovery-and-help.md) | [descriptions-structure-and-length](mcp/descriptions-structure-and-length.md) |
| 4 Steering | [continuation-modes](cli/continuation-modes.md) | [steering-contract](decisions/steering-contract.md) |
| 5 Safety | [non-interactive](cli/non-interactive.md), [auth-and-secrets](cli/auth-and-secrets.md) | [security/least-privilege-and-confirmation](mcp/security/least-privilege-and-confirmation.md) |
| 6 Budget | [field-selection](cli/field-selection.md), [pagination](cli/pagination.md) | [budget-tool-definitions](mcp/budget-tool-definitions.md), [budget-response-size](mcp/budget-response-size.md) |
| 7 Recovery | [error-classes](cli/error-classes.md), [retry](cli/retry.md) | [errors-framing-and-recovery](mcp/errors-framing-and-recovery.md) |
| 8 Verification | [non-interactive](cli/non-interactive.md) | [ops-testing-layers](mcp/ops-testing-layers.md) |

Choosing the surface itself (CLI, MCP or skill): [surface-choice](decisions/surface-choice.md).
