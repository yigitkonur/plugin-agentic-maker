# Skill frontmatter: portable fields and Claude Code fields

> Read when: you write or edit a SKILL.md frontmatter block and must decide which fields to use, or a validator or upload rejects a field.

Two field sets exist. The portable set is defined by the open spec at agentskills.io and is read by every harness. The Claude Code set adds fields that only Claude Code acts on. Pick the set first, then the fields.

## Choose the set

| The skill must run in | Use |
|---|---|
| Claude Code only (own plugin or `.claude/skills/`) | portable fields plus any Claude Code field |
| Several harnesses (Cursor, Codex, Copilot, others) | the 6 portable fields only |
| Claude.ai upload or the Skills API | the 6 portable fields only; any other key is a hard error at packaging or upload |

Claude Code ignores unknown fields without an error. Strict portable validators (`skills-ref validate`) and uploads reject them. A skill that passes in Claude Code can still fail elsewhere, so check the target harness, not only Claude Code.

Rules for both sets:

- The file is named `SKILL.md` and sits in a directory named after the skill.
- Frontmatter starts on line 1 of `SKILL.md`, between `---` lines. A blank line first makes Claude Code treat the whole file as body text.
- If the YAML does not parse, Claude Code loads the skill with no fields set.
- Keep `<` and `>` out of `name` and `description`. Claude Code refuses a `name` containing them.
- Booleans take `true`/`false` (Claude Code 2.1.218+ also accepts `yes/no`, `on/off`, `1/0`). Write `true`/`false` for portability.

## Portable core (6 fields)

| Field | Required | Limit and format |
|---|---|---|
| `name` | yes | 1 to 64 characters; `a-z`, `0-9`, `-`; no leading, trailing or double hyphen; equals the parent directory name |
| `description` | yes | 1 to 1024 characters; say what it does and when to use it |
| `license` | no | short SPDX name or a bundled file name |
| `compatibility` | no | 1 to 500 characters; environment needs (packages, network) |
| `metadata` | no | map of string to string; put custom keys here (`author`, `version`) |
| `allowed-tools` | no | space-separated patterns, e.g. `Bash(git:*) Read`; experimental in the spec |

Minimal valid portable skill, in `<skill-name>/SKILL.md`:

```yaml
---
name: my-skill
description: Write release notes from a list of commits. Use when asked for release notes or a changelog.
---
```

Claude Code reads only `name`, `description`, and `allowed-tools` from this set; `license`, `compatibility` and `metadata` are accepted and not acted on.

## Claude Code-only fields

The Claude Code docs state no length limit for `name`; keep to the 64-character portable limit anyway. If `name` is omitted it defaults to the directory name; if `description` is omitted it defaults to the first non-empty body line, so always write it.

| Field | Effect |
|---|---|
| `when_to_use` | extra trigger text appended to `description` |
| `argument-hint` | autocomplete hint, e.g. `[issue-number]` |
| `arguments` | named positional arguments for `$name` substitution |
| `disable-model-invocation` | `true`: the model cannot load it (also not preloaded into subagents); the user starts it with `/name` |
| `user-invocable` | `false`: hidden from the `/` menu; only the model starts it |
| `allowed-tools` | tools usable without a permission prompt for the turn that invokes the skill; the grant clears at your next message; also accepts commas or a YAML list |
| `disallowed-tools` | tools removed while the skill is active; clears at your next message |
| `model` | model for the current turn (`inherit` allowed); with `context: fork`, the subagent's model |
| `effort` | `low`, `medium`, `high`, `xhigh`, `max`; levels depend on the model |
| `context` | `fork`: run the skill in a forked subagent |
| `agent` | subagent type for `context: fork`: `Explore`, `Plan`, `general-purpose` (default) or a custom agent |
| `background` | only with `context: fork`; default `true` runs in the background, `false` waits for the result in the same turn (needs 2.1.218+) |
| `hooks` | hooks registered when the skill is invoked, kept for the session; schema is in the Claude Code hooks docs |
| `paths` | globs (comma-separated string or YAML list); the model auto-loads the skill only when working with matching files under the current directory |
| `shell` | shell for inline `` !`command` `` blocks: `bash` (default) or `powershell` |

`description` plus `when_to_use` is cut at 1,536 characters in the skill listing. Put the main trigger first. Aim far below the cap: see `skills/agent-interface-design/references/skill/descriptions-that-trigger.md`.

Minimal valid Claude Code skill, user-started and run in a subagent:

```yaml
---
name: audit-deps
description: Audit project dependencies for outdated or vulnerable packages. Use when asked to check dependencies.
disable-model-invocation: true
argument-hint: "[path]"
context: fork
agent: Explore
allowed-tools: Read Grep Bash(npm audit:*)
---
```

## Keep a Claude Code field out of a portable skill

- Name the field in the portable replacement before you drop it. `disable-model-invocation` has none: say in the description when to use the skill, and accept that other harnesses may load it on their own.
- Put custom keys under `metadata:` (string values only).
- Do not rely on `hooks`, `context: fork` or `paths` for correctness in a portable skill; write the body so it still works when they are ignored.
- Check both sets: `claude plugin validate <skills-dir>` (2.1.233+) reports frontmatter that fails to parse but does not flag unknown fields; `skills-ref validate ./my-skill` is the check for the portable core.

## After editing

Run `/agentic-maker:derail <skill-dir>` to see whether fresh agents choose the skill and follow it. The body text rules are in `skills/agent-interface-design/references/skill/text-as-program.md`.
