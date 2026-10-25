# Structure of strong skills, annotated

> Read when: you are laying out a new skill (files, routing, how big) and want a skeleton to copy before you write any text.

Four skeletons, from smallest to largest. Pick the one that matches the job, cut it to fit, then write the text. For the description wording see `skills/agent-interface-design/references/skill/descriptions-that-trigger.md`; for the body wording see `skills/agent-interface-design/references/skill/text-as-program.md`.

## 1. Micro-skill: one job, two formats

```
init-agent-config/
├── SKILL.md                 # ~120 lines
└── references/
    ├── claudemd-format.md
    └── agentsmd-format.md
```

SKILL.md sections, in order:

1. Decision tree, 3 branches: create A, create B, audit (audit reads both files plus the checklist below).
2. Quick start: a 15-line template inline.
3. Audit checklist: about 20 lines of validation steps.
4. Guardrails: about 5 lines.

Why this works: the common case (create from template) needs no file load, and each reference holds exactly one format.

## 2. Phase-routed skill: a multi-step workflow

```
build-thing/
├── SKILL.md                 # ~200 lines, one section per phase
├── scripts/                 # download and research helpers
└── references/
    ├── <phase-1>.md         # research
    ├── <phase-2>.md         # compare
    ├── <phase-3>.md         # synthesize
    ├── <phase-4>.md         # ship
    └── anti-patterns.md     # what not to do
```

Why this works: the phases (research, compare, synthesize, ship) follow the order the work happens in, so the agent opens the page for the current phase. Mechanical steps live in `scripts/`. A dedicated anti-patterns page states what not to do explicitly instead of scattering it. Reuse proven workflow pages and add structure around them rather than rewriting.

## 3. Tool-wrapping skill: workflow on top of an MCP server or CLI

```
code-review-with-tool/
├── SKILL.md                 # ~200 lines
└── references/
    ├── analysis.md          # how to read the tool's output
    ├── workflow.md          # fetch -> analyze -> propose -> open PR
    └── troubleshooting.md   # tool API failures and how to handle each
```

Why this works: the tool already gives raw access, so the skill carries only what the tool cannot: the order of calls, how to interpret results, what a good outcome looks like, and what to do when a call fails.

## 4. Large reference skill: an SDK or product surface

```
build-sdk-app/
├── SKILL.md                 # 250-400 lines
└── references/
    ├── <area-1>/            # one folder per top-level category
    │   └── <task>.md        # one task per file
    └── ... (about 10 folders, 40+ files)
```

SKILL.md carries, in this order:

| Block | Size | Job |
|---|---|---|
| Decision tree | exactly 3 levels, never deeper: category, task, file (80+ leaves) | Agent finds one file in one scan |
| Quick start | 3 short examples (basic, streaming, custom tool) | Covers most first tasks without a file load |
| Key patterns | about 7 essential patterns with code | Shows canonical usage |
| Pitfalls table | about 10 rows, `Pitfall / Fix` | Fix in the same row as the problem |
| Reading sets | 3 to 6 files per set | Named by user intent, in quotes |
| Final reminder | short closing paragraph | Load the smallest set first, expand only on need |

Name each reading set by what the user says ("I need a basic app with custom tools"), not by a technical category. The folders in `references/` mirror the tree's top-level categories so the path is predictable.

## Parts that carry over to every size

- **Pitfalls as a table, not prose, with the fix in each row.**
- **Guardrails as "Do not ..." bullets** that name a checkable behavior ("Do not claim research happened unless the comparison table appears in the output").
- **Inline what every run needs; route the rest.** Anything used in fewer than half of runs goes to a reference.
- **Standalone skills** (no MCP, no scripts) carry value in embedded expertise: a style guide in the instructions, a quality checklist before finalizing, detail in references.

## Sizing

| Skill type | SKILL.md lines | Reference files | Total files |
|---|---|---|---|
| Micro | 50-120 | 1-3 | 2-4 |
| Standard | 150-250 | 4-8 | 5-10 |
| Comprehensive | 250-400 | 10-40 | 12-45 |

Start at the smallest row that fits the job. Grow when a derailment run shows the agent missing something: `/agentic-maker:derail <skill-dir>`. Audit the result with `/agentic-maker:audit <skill-dir>`.
