# Name a skill and decide its boundaries

> Read when: you pick a name for a new skill, rename one, or are deciding whether to split one skill into two or merge two into one.

A skill's name and its boundary are one decision: the name says what the skill does, so a skill you cannot name in two or three words probably does two jobs. Settle both before writing the body.

## Naming rules

Apply all of these. The directory is the skill's identifier in file listings; `name` is what the `/` menu shows.

| Rule | Good | Bad |
|---|---|---|
| Kebab-case: lowercase letters, digits, single hyphens (`^[a-z0-9]+(-[a-z0-9]+)*$`) | `audit-completion` | `Audit_Completion`, `auditCompletion` |
| No leading, trailing or doubled hyphen | `my-skill` | `-my-skill`, `my--skill` |
| 64 characters at most; most names fit in 20 to 40 | `build-mcp-server` | a 70-character sentence |
| Verb first, then the thing it acts on | `build-mcp-server` | `mcp-server` |
| No version, date or "new" in the name | `handle-auth` | `v2-new-auth-handler` |
| Directory name equals frontmatter `name` | `skills/build-skill/` with `name: build-skill` | folder `pdf-tools-v2/` with `name: pdf-tools` |

The Agent Skills specification requires the kebab-case form, the 64-character cap and the directory match. Claude Code itself does not require the match: `name` is optional and defaults to the directory name, and the directory name also invokes the skill. Keep them identical anyway: two identifiers for one skill make renames, cross-references and `agentic-maker scan skill` output ambiguous.

Claude Code refuses `<`, `>`, control characters and non-standard blanks in `name`. It reserves `anthropic-skills` and a folder named `synced`; do not use either. Also avoid `claude` or `anthropic` as a name prefix: claude.ai rejects such skill names on upload.

Inside a plugin the skill is invoked as `/<plugin>:<name>`. Do not repeat the plugin name inside the skill name (`agentic-maker:derail`, not `agentic-maker:agentic-maker-derail`).

### Verb choice

Use the verb that matches what the skill produces, and use it the same way across the plugin.

| The skill... | Start with | Example |
|---|---|---|
| creates something new | `build-`, `create-` | `build-skill` |
| checks something and reports | `audit-`, `run-review` | `audit-completion` |
| runs a tool or procedure | `run-` | `run-ts-cleanup` |
| sets up a project or tool once | `init-`, `setup-` | `init-agent-config` |
| turns one format into another | `convert-<source>-to-<target>` | `convert-url-to-nextjs` |
| investigates a problem | `debug-`, `research-` | `debug-provider-routing` |

### Check the name against the crowd

Names appear in the skill listing beside every other skill. Replace a name that fails either check:

- It names a noun only (`mcp-server`, `helper`, `tools`): add the verb and the target.
- Another installed skill differs from it by one word: make the difference the first thing a reader sees.

How to write the description that goes with the name: `skills/agent-interface-design/references/skill/descriptions-that-trigger.md`.

## Split or merge

Decide from how the skill is used, not from how big it feels. Count first:

```bash
wc -l skills/<name>/SKILL.md skills/<name>/references/*.md
ls skills/<name>/references | wc -l
```

### Split one skill into two when

Several of these hold together:

- The workflows are independent: running one never needs the other.
- Users trigger them with different phrases (the description would need an "or" joining two unrelated jobs).
- The tool grants differ: one needs pre-approved `Bash` or write access, the other none (`allowed-tools` is set per skill and pre-approves tools; it does not restrict them).
- The references do not overlap: no reference file is read by both workflows.
- `SKILL.md` would pass 500 lines even after you move detail into references. Over 500 alone means "move detail to `references/`" first; split only if the other signals also hold.

Example: "create app" and "deploy app" in one skill. Nothing in deploy needs the create steps, so `create-app` and `deploy-app` are two skills.

### Merge two skills into one when

Several of these hold together:

- They share reference files, or you copied the same paragraph into both.
- Users naturally combine the two tasks in one session, or one always runs right after the other.
- Skill A's description has to say "requires skill B".
- Their descriptions are nearly identical, so the agent picks between them by chance (a T2 collision in a derailment run).
- The combined `SKILL.md` would stay under about 300 lines, or splitting would leave each skill with only one or two references.

### If you cannot decide

Keep one skill, and give `SKILL.md` a decision table that routes to separate reference files. Split later when the signals above hold.

### Dependencies between skills

If skill A requires skill B, in order of preference:

1. Merge them into one skill.
2. Name B in A's description.
3. Avoid sharing reference files between the two: a file that both need means they are one skill, and shared files couple them.

## Cross-references

Refer to another skill by its `name`, in plain text: "for server setup, use the `build-mcp-server` skill". Do not link to its directory path; the agent resolves the name to the skill.

## Check the result

1. Run `agentic-maker scan skill` and confirm the new or renamed skill is listed once, at the path you expect.
2. Confirm the `# Title` of `SKILL.md` reads as the human-readable form of `name`, and any README label for the skill equals `name`.
3. Run `/agentic-maker:derail <skill-dir>` with an everyday request that does not mention the skill. If a neighbour wins (T2) or nothing is chosen (T1), fix the name and description before touching the body; the repair table is in `skills/agent-interface-design/references/skill/descriptions-that-trigger.md`.
4. After a split, merge or rename, grep for the old name: `grep -rn "<old-name>" skills/ commands/ README.md`. Zero hits is the pass condition.

Rules for the body once the boundary is fixed: `skills/agent-interface-design/references/skill/text-as-program.md`.
