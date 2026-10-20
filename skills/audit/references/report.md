# The audit report

> Read when: you write the final message of an audit.

One report per surface, in this order. It is the whole deliverable; an audit changes nothing.

1. **Header.** Target, kind (CLI / script / MCP server / skill / plugin), date, the probe version (`agentic-maker --version`), and what machine facts matter (`doctor`).
2. **Scorecard.** The eight dimensions of the contract with their score or `not measured`, and the overall score from [scoring](scoring.md).
3. **Findings, most severe first.** For each: severity; one-line statement; **evidence** (the probe output with the exact command, or `path:line`, or a labelled assumption); **impact** in agent terms (what the agent will do wrong); **fix** (concrete, small); **how to verify** (the exact probe or command to rerun and what it should show).
4. **What was run.** The commands the probe executed, verbatim, and what each told you.
5. **What was not run, and why.** Commands left out because they could change state, servers not connected, files not read. Include the limits the probe states about itself.
6. **Assumptions.** Anything inferred rather than observed.
7. **Next step.** Which findings to fix first, and whether `/agentic-maker:derail <target>` is worth running to see the behaviour (it is, for descriptions, steering and recovery, which only show up in a run).

The CLI and MCP workflows add their own checklists: [cli-audit-workflow](cli-audit-workflow.md), [mcp-audit-workflow](mcp-audit-workflow.md).
