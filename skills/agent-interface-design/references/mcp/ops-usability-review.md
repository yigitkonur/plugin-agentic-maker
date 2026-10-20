# Ask the model to review your server's usability

> Read when: you changed a schema or description, notice the model using workarounds, or are about to finalize tool descriptions for production.

<!-- src: audit-agentic-mcp/references/patterns/testing.md#4. Ask the LLM to Evaluate Your Server's Usability -->
## The model is your user

The model is your user. Ask it directly how to improve usability and tool documentation. AI UX is underappreciated and trivially easy to measure by simply asking.

The feedback loop: give the model the tool schemas, then ask:

```
You are using these MCP tools: [paste tool schemas]

1. Which tool descriptions are confusing or ambiguous?
2. Which parameter names don't match how you'd naturally think about the task?
3. Where do you feel uncertain about what a tool does or when to use it?
4. If you could redesign this interface from scratch, what would you change?
5. Here are two versions of a description -- which is more pleasant to use?
```

A/B test descriptions in context: present two variants and ask the model to pick and explain why. Example pair from the source:

- Version A: "Searches the database for matching records."
- Version B: "Find records matching your criteria. Returns up to 50 results sorted by relevance. Use filters to narrow: status, date_range, owner."

Ask: "Which description would help you use this tool more effectively? Why?" Python wrapper: `../frameworks/mcp-python/testing.md`.

What this catches that evals miss:

- A subtle usability gap: the model "works around" a bad description instead of failing.
- Missing context: the model wishes it knew what format a parameter expects.
- Naming mismatch: the model's mental model does not match your parameter names.
- Ambiguous boundaries: the model cannot tell when to use tool A versus tool B.

When to run this:

- After every significant schema change.
- When you notice the model using workarounds or extra tool calls.
- Before finalizing tool descriptions for production.

Key insight: the model will not complain unprompted; it adapts silently. You have to explicitly ask for critique. Treat it like a user interview, not a bug report. For description length and structure, see `descriptions-structure-and-length.md`.

Sources: r/mcp community threads on LLM-as-user feedback.
