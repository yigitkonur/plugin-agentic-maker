# Target: a skill

> Read when: the target is a skill directory (a `SKILL.md` with or without references and scripts).

**Exposure:** `--plugin-dir` (a loose skill is wrapped in a generated plugin whose name you set with `wrapper_name`), `--add-dir` so the worker can read the skill's own files. The prompt never names the skill, with one exception: a skill with `disable-model-invocation: true` cannot be chosen by a worker, only started by a slash command, so its prompt has to begin with `/<wrapper_name>:<skill>` (the dry-run tells you the exact form). Such a run tests what happens after the skill starts; whether it would be chosen (T1) cannot be observed for it.

**Lens, in order:**
1. **Trigger (T1-T3).** Was the skill chosen? The listing the worker saw is in `env.json`; the description is the only thing it had to decide with (plus the name). Several takes: report the rate.
2. **Discovery (S3, S4).** Did it open the files the text points to? Which references were never read?
3. **Following (M1-M6, S1, S2).** Where did it guess a threshold, a path, a format? Where did two instructions conflict, and which one won?
4. **Execution (O1-O5).** Scripts the skill ships: do the documented command lines work from the directory the worker is in?
5. **Completion (C1, C4).** Does "done" match the receipts?

**Typical scenarios:** a normal task in a user's words; an ambiguous one; one with a missing prerequisite. A skill with a `references/` directory also needs a scenario that can only be solved by reading one.

To write or redesign the skill under test, use `/agentic-maker:build-skill`; this page is for testing it.

**Do not** test by telling the worker "use the X skill".
