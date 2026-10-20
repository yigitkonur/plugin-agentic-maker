# MCP prompts as repeatable workflow entry points

> Read when: users keep typing the same complex instruction, or you are deciding whether a recurring workflow should be an MCP prompt, a tool, or both.

<!-- src: audit-agentic-mcp/references/patterns/resources-and-prompts.md#3. Use MCP Prompts for Repeatable Workflow Entry Points -->
## Ship recurring workflows as prompts

Prompts are user-controlled templates that combine instructions, parameters and attached resources into a reusable workflow trigger. They remove the "I keep typing the same complex instruction" problem. The example is a bug-analysis prompt that takes `error_message`, `file_path` and `severity` (default `medium`), returns a first message with numbered steps (identify the root cause; check related issues in nearby code; propose a fix with test cases; assess risk of the fix) and a second message that embeds the source file as a resource (`file://<path>`, `text/plain`). Code: `../frameworks/mcp-python/resources-and-prompts.md`.

Prompts versus tools:

- Prompts are user-initiated: the user selects them from a menu.
- Tools are model-initiated: the model decides to call them.
- Prompts can embed resources directly, providing data alongside the instructions.
- Prompts act as saved workflows the user can trigger repeatedly.

Real-world uses:

- a sequential-thinking server with prompts for architecture design, bug analysis and refactoring;
- test-generation prompts that include the source file as a resource;
- code-review prompts with embedded style guides.

Limitation: most clients do not fully support persistence of prompt template values yet, so assume the user re-enters arguments each session. Per-client detail: `../fresh/mcp-resource-prompt-client-support.md`.

When prompt arguments have a known finite set, implement completion for them: `protocol-roots-and-completion.md`.

Sources: MCP specification (prompts).
