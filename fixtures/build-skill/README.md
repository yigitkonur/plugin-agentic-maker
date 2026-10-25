# Derail scenarios for `/agentic-maker:build-skill`

Four use cases, run from this folder (the scenarios point at the plugin with `target: ../..`):

| Scenario | The worker is asked to | What its receipts check |
|---|---|---|
| `new-from-doc` | write a skill for an internal CLI from a local doc | facts from the doc, frontmatter, size, links, doc untouched |
| `redesign` | fix a skill with a name that differs from its folder, `<` in the description, a dead link, a script path that only works from the skill folder, and a pile of "never" rules | each of those fixed at its cause, references and script kept |
| `merge` | merge two skills into one | both commands survive exactly, sources untouched |
| `from-conversation` | distil a chat log into a skill | the corrections are in it, in order, one new skill |

```
cd fixtures/build-skill
agentic-maker run <scenario> --dry-run     # preview, no spend
/agentic-maker:derail <the plugin dir> ...  # the whole loop, in a session with the plugin loaded
```

The prompts start with `/agentic-maker:build-skill` because that skill can only be started by a user.
