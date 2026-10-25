# Workflow and decision-tree patterns inside a skill

> Read when: you are choosing how to lay out the body of a skill (steps, loop, branches or a routing table), or a derailment run shows an agent doing steps out of order, looping without end, or opening the wrong reference.

A skill body has one dominant shape. Pick it before writing prose. Other shapes nest inside it (a loop inside step 3, a branch inside step 1), but `SKILL.md` shows only the dominant one; push nested detail into a reference.

## Choose the shape

```
Does the agent do the same steps, in order, every time?
|-- yes: does the output need checking and repair before it is done?
|        |-- no  -> 1. Sequential
|        `-- yes -> 2. Iterative with a gate
`-- no: does the first step depend on what the input is?
         |-- yes, the input picks one of a few procedures -> 3. Branching by input
         `-- yes, the input picks one topic out of many  -> 4. Routing to references
```

If two answers fit, take the lower number and nest the other inside it.

## 1. Sequential

Use when steps have a fixed order and each needs the output of the one before (setup, release, migration).

```markdown
## Steps
1. Run `scripts/check-env.sh`. Expect: prints `ok`. If not, stop and report its output.
2. Create `out/plan.md` from the template. Expect: file exists, 1+ lines.
3. Apply the plan. Expect: `git diff --stat` shows only files listed in `out/plan.md`.
4. Report: files changed, one line each.
```

Rules: number the steps; name the input each step reads; end each step with a command and its expected result; say what to do when the result is wrong (stop, or go back to step N).

Prevents: skipped steps, out-of-order execution, and a failure at step 2 surfacing as a confusing error at step 5. If a step is skipped on purpose, the report says which and why ("steps 4-6 skipped: local-only change"), so a reader can tell omission from accident.

## 2. Iterative with a gate

Use when the first draft is rarely right and "right" can be measured (generated docs, code that must lint, a report with required sections).

```markdown
## Loop
1. Draft to `out/draft.md`.
2. Gate: run `scripts/check.py out/draft.md`. Pass = prints `0 problems`.
3. If it fails: fix only the lines the gate names, then repeat step 2.
4. Stop after 3 failed gates. Report the last gate output; do not ship `out/draft.md`.
5. On pass: copy to `out/final.md`.
```

Rules: the gate is a command or a short checklist of yes/no items, never "make it good"; fix the cap as a number (3 is typical); keep draft and final in different paths; define what happens at the cap.

Prevents: endless polishing, "looks fine" self-approval, and a half-fixed draft being shipped as final. Prefer a script gate over a judgement gate; a judgement gate needs the criteria written out.

## 3. Branching by input

Use when one request has a few different procedures and the input decides which (file type, size, environment, flag present).

```markdown
## Pick the procedure
Check in this order and take the first match:
1. `$ARGUMENTS` is a directory -> **Directory mode**, below.
2. `$ARGUMENTS` ends in `.json` -> **JSON mode**, below.
3. Anything else -> ask the user for a directory or a `.json` file, then stop.
Say which branch you took and why in one line before starting it.
```

Rules: tests are concrete and checkable by a command (`test -d`, extension, byte count), not by feel; order by how common each case is; branches are mutually exclusive or explicitly first-match; the last branch is a default or a stop, never nothing; each branch holds a full sequential procedure or points to one.

Prevents: the agent blending two procedures, picking by guess when the input is odd, and branches that overlap so two apply. When the branches grow into many topics, use shape 4.

## 4. Routing to references

Use when the skill covers many topics and any one run needs only one or two (an SDK, a toolbox, a style guide).

```markdown
## Read before you act
| Task | Read |
|---|---|
| Add a login screen | `references/auth/login-flow.md` |
| Refresh an expired token | `references/auth/token-refresh.md` |
| Fix a build error | `references/debug/build-errors.md` |
Read the matching file fully, then act. If no row matches, say so and ask.
```

Rules:
- Rows are tasks in the user's words, not file names. "Options" -> `options.md` cannot be told apart from its neighbours; "Client constructor options" can.
- Every file under `references/` appears in some row; an unlisted file is dead weight.
- Each file holds one decision and opens with a line saying when to read it.
- Order rows by how often they are needed. Keep to 3 levels of nesting at most.
- A topic of under 20 lines that every run needs stays inline in `SKILL.md`; do not make a one-paragraph file.
- Rows must not overlap; if two rows could match one task, merge them or sharpen the wording.

Prevents: `SKILL.md` growing until the agent skims it, the agent reading all references "to be safe", and the agent reading the wrong one because labels were vague.

## Check the shape

- Each phase boundary should leave a visible artifact (a file, a printed result); if output appears only at the end, add a checkpoint.
- For each file under `references/`, run `grep -c <file-name> SKILL.md`; a 0 means no row points to it.
- Run `/agentic-maker:derail <skill-dir>` with a task that hits each branch and one that matches none; read where fresh agents hesitated and rewrite that text.
- For how to word the steps themselves (paths, numbers instead of adjectives, a check on each phase) see `skills/agent-interface-design/references/skill/text-as-program.md`. For the description that makes the skill get chosen at all see `skills/agent-interface-design/references/skill/descriptions-that-trigger.md`.
