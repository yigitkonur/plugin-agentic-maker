# New CLI interview

> Read when: the surface chosen in step 1 is a CLI or script an agent will run, and you are about to ask the user what it must do.

Paths in this file are relative to `${CLAUDE_PLUGIN_ROOT}/skills/agent-interface-design/references/`. Ask in these words, one group of up to four at a time. The closed ones go through `AskUserQuestion` with the options listed; the open ones are plain text, because that tool offers choices, not free text. Fill from what the user already said and from the project (`agentic-maker detect`) and confirm instead of asking again.

## Group 1: the job

1. **Task (open).** "What should the agent be able to do with this, in one sentence? Describe the outcome, not the commands."
2. **Existing tool (open).** "Does an official CLI or a maintained SDK already do part of it (`gh`, `kubectl`, `aws`, `stripe`)? If yes, say which." If yes, read `decisions/surface-choice.md` first: wrapping or fixing the existing one may be the answer.
3. **Who runs it (closed).** Options: the agent in its own shell; a CI job; a person and an agent both; a pipeline of other tools.
4. **Language and distribution (closed).** Options: a script in the repo; a single binary; a package (npm, pip, cargo); not decided.

## Group 2: the contract

5. **Output (closed).** Options: one result per call (a JSON envelope); a list that can be long (pagination, `--fields`); a stream of progress and a final result (JSONL); plain text is enough.
6. **Credentials (closed).** Options: none; an environment variable; a token file; a browser or device login. A secret is never an argument (`cli/config-and-env.md`).
7. **Destructive operations (closed, several).** Options: deletes data; sends something to people; spends money or deploys; none. Each one gets `--dry-run` and an explicit `--yes` (`cli/dry-run.md`, `cli/non-interactive.md`).
8. **Success (open).** "How will you know in a month that agents use it well? A task that works first time, an error rate, steps per task?"

## Then

Sketch with `cli-deliverables.md` (grammar, flags, stdout and stderr rules, envelope, exit codes) and check the sketch against the eight questions in `contract.md`. Wait for the user's approval before any code. When it is built, `agentic-maker probe cli <binary> --safe "<read-only args>"` is the first check, `/agentic-maker:audit` the full report.
