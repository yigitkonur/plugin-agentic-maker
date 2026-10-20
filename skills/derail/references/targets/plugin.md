# Target: a plugin

> Read when: the target is a whole plugin - several skills, agents, hooks - or when a plugin tests itself.

**Exposure:** `--plugin-dir <plugin root>` (and `--add-dir`); `--include-hook-events` is already on, so hook firing is in the trace.

**Lens:**
1. **Routing across skills.** With several skills loaded, did the right one win (T2), or did none (T1)?
2. **Hooks.** Did each hook fire when it should, stay silent when it should, and never block the agent without a way out? Count hook events per take; a hook that fires on every turn is noise.
3. **Subagents.** Was the agent used, with the right inputs? Did its output come back in a usable shape?
4. **Footprint.** What is always in context? `claude plugin details <name>` prints the component inventory and projected always-on cost; compare it to what the plugin earns.
5. Everything in the skill lens, per skill.

**Dogfood:** this plugin is derailed with this plugin: the two knowledge skills (`agent-interface-design`, `derailment-method`) and the CLI. The Stop gate's own behaviour is tested by editing a target and trying to close without a fresh run.
