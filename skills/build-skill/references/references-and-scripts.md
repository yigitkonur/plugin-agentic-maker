# Split a skill into SKILL.md, references and scripts

> Read when: a SKILL.md is growing past about 300 lines, you decide where a piece of content belongs (SKILL.md, a reference file or a script), or a derailment run shows an agent never opening a file or running a script wrong.

Three places hold skill content. Each loads differently, so each gets a different kind of content.

| Part | Loads | Put here |
|---|---|---|
| `SKILL.md` | Whole body when the skill is invoked, then stays in context | The decision, the steps, the routing table |
| `references/*.md` | Only when the agent reads the file | Detail needed in some runs, not all |
| `scripts/*` | Run with Bash; the code is not loaded, only its output | Steps with one right answer |
| `assets/*` | Referenced by path, not read | Templates, images, static files |

The skill listing shows only `description` and `when_to_use`, cut at 1,536 characters combined (see `skills/agent-interface-design/references/skill/descriptions-that-trigger.md`). Everything else costs nothing until the skill is chosen. After auto-compaction only the first 5,000 tokens of an invoked SKILL.md are kept, so put the routing table and the critical steps early.

## What stays in SKILL.md

Keep SKILL.md under 500 lines.

Keep:
- The job in one or two sentences and the dominant workflow (numbered steps or a decision tree).
- Everything needed by 80% of runs, so the common case needs zero extra reads.
- The routing table to references (skeleton below).
- The full command line of every script (see below).

Move out anything that fits one of these:
- Used by fewer than half of the runs (edge cases, rare formats, long examples).
- A lookup table or schema over 20 rows.
- Background that explains why but changes no step.
- A second workflow that starts from a different user request.

Do not keep the same text in SKILL.md and in a reference. Keep it in one place and point to it.

## What moves to references/

- One decision or topic per file. If the title needs "and", make two files.
- Size: 30 to 80 lines for a single pattern, 100 to 250 for a topic guide, up to 400 for a complex topic. Split any file past 400 lines: by sub-topic, by depth (quickstart and advanced), or by moving lookup tables out.
- One hop only: SKILL.md links the file, the file ends the reading. A reference may mention another file, but the agent must be able to act without opening it. If A cannot be used without B, merge them.
- Folders: flat `references/` for 6 files or fewer. Above that, one category level (`references/<topic>/<file>.md`), never deeper. Do not name a file `README.md`.
- Names: kebab-case, under 50 characters, no version numbers, no repeat of the folder name.
- First lines: `# Title`, then one line saying when to read the file, so the agent can confirm relevance before reading on.
- Over 300 lines: open with a short contents list of the H2 sections.

Agents should load only the 3 to 5 files for the current step. Reading more than 5 references before producing any output is over-loading; load more in the next step, not up front. Mention references by path relative to the skill root (`references/<category>/<file>.md`) and never make two references point at each other.

## The routing table

Every file in `references/` must be named in SKILL.md with a "read when" condition. An unrouted file is never read. Skeleton:

```markdown
## Reference files

| Read | When |
|---|---|
| `references/<topic-a>.md` | You are about to <action>, or <symptom> appears. |
| `references/<topic-b>.md` | The input is <unusual case>. |
```

For tasks that need several files, add a named set under the table:

```markdown
Setting up from scratch: `references/<topic-a>.md`, then `references/<topic-b>.md`.
```

Write the condition as a situation the agent can recognise ("the config file already exists"), not a topic ("configuration").

Check for orphans from the skill directory:

```bash
for f in $(find references -name '*.md'); do grep -q "$(basename "$f")" SKILL.md || echo "ORPHAN: $f"; done
```

Check sizes: `find references -name '*.md' -exec wc -l {} + | sort -rn | head -5`.

## What becomes a script

Write a script when the step is deterministic: the same input must give the same output, and the agent would otherwise retype or re-derive it each run. Typical cases: converting a format, validating against a rule, computing a number, scaffolding a folder, calling a CLI with fixed arguments.

Keep it as prose when the step needs judgment (choosing a name, summarising, deciding what to include). A script that guesses is worse than text.

A script must meet all of these before the skill ships:
- **Language:** Python 3 (standard library only) or Node (`.mjs`), so there is no build or install step. Avoid shell scripts that depend on GNU-only flags.
- **Tested with real input:** run it on a real file or a copy of one, not a made-up string. Confirm exit code 0 on good input and a non-zero exit with a one-line message on bad input.
- **Self-describing failure:** print what is wrong and what to do next. The agent reads that line and acts on it.
- **Read-only unless it must write:** if it writes, it writes only to a path passed as an argument.

## Write the command line out in full

Bash commands run in the session's working directory (normally the user's project, and it moves if the agent runs `cd`), not the skill folder. A bare `scripts/run.py` fails. In SKILL.md write the whole command, with the skill directory variable, every argument and the expected result:

```markdown
Run from the project directory:

    python3 ${CLAUDE_SKILL_DIR}/scripts/check.py <input-file> --out <report-file>

Expect: `OK: <n> rows` and exit code 0. On `ERROR:` read the message, fix the input, run again.
```

Rules for the line:
- Use `${CLAUDE_SKILL_DIR}`. It is substituted in skill content and expands to the directory holding that skill's `SKILL.md`; in a plugin skill that is the skill's own folder, not the plugin root. Use `${CLAUDE_PLUGIN_ROOT}` for files shared across the plugin.
- Show placeholders in angle brackets.
- State the expected output so the agent can tell success from silence.
- One command per step, with no shell variables, so one `allowed-tools` pattern covers it: `allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/check.py *)`.
- Never write "run the script in scripts/" or "see scripts/ for helpers". Naming the file without the command forces a guess.

## Verify the split

1. Run the orphan check and the size check above.
2. Run `/agentic-maker:derail <skill-dir>` with fresh agents: look for a reference never opened when it should have been (fix the "read when"), a script run with a wrong path (fix the command line), and steps re-derived by hand that a script covers.
3. Run `agentic-maker scan skill <skill-dir>` or `/agentic-maker:audit <skill-dir>` for structure findings.

For wording of the steps themselves, see `skills/agent-interface-design/references/skill/text-as-program.md`.
