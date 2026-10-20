# Input schema robustness: coercion, regex errors, safe names, portability

> Read when: models send wrong types, a regex-constrained field keeps failing, a tool name may break a client, or the server must work across several LLM clients.

Companion to `schemas-flat-and-sized.md` (shape and size). Code (TypeScript): `../frameworks/mcp-ts/schema-design.md`, `../frameworks/mcp-ts/schema-design-portability.md`.

<!-- src: audit-agentic-mcp/references/patterns/schema-design.md#Pattern 1: Use `z.coerce` and `z.preprocess` for Type Safety | audit-agentic-mcp/references/patterns/schema-design.md#Coerced Number | audit-agentic-mcp/references/patterns/schema-design.md#Coerced Boolean | audit-agentic-mcp/references/patterns/schema-design.md#Why This Matters -->
## Coerce types at the schema level

LLMs frequently send `"3"` instead of `3`, or `"false"` instead of `false`. Without coercion the server throws a validation error, the LLM sees a cryptic message, and the request fails silently. Fix it in the schema (Zod names: `z.coerce`, `z.preprocess`; the idea applies to any validator).

- **Coerced number:** accept `"3"`, `3` and `"3.5"` (`z.coerce.number()` instead of `z.number()`).
- **Coerced boolean:** accept a real boolean, or the strings `"true"`/`"false"` case-insensitively; pass anything else through to fail normally. A reference sequential-thinking server uses this to handle every boolean variant an LLM might send. Then `includeArchived` can be `optional().default(false)` and is always a real boolean in the handler.

Why it matters:
- LLMs serialize all tool arguments as JSON; type-coercion bugs are the #1 cause of silent tool failures.
- Coercion is zero-cost at runtime and removes a whole class of errors.
- The alternative, sending back a validation error, wastes a round-trip and confuses the model.

<!-- src: audit-agentic-mcp/references/patterns/schema-design.md#Pattern 2: Pair Regex Validation with Human-Readable Examples | audit-agentic-mcp/references/patterns/schema-design.md#Apply This to Any Format Constraint -->
## Pair a regex with a human-readable example

The LLM never sees your regex; it only sees the error message on failure. Make that message a working example it can copy.

- Bad: `nodeId` regex `/^I?\d+[:|-]\d+/` fails with "Invalid input"; the model has no idea what is expected.
- Good: same regex, message "Node ID must be like '1234:5678' or 'I5666:180910;1:10515'". A design-tool server uses this for its non-obvious node-ID format, and the model self-corrects on the next attempt.

Apply it to every format constraint:
- Hex color: "Must be hex color like '#FF5733' or '#00aa99'" (`/^#[0-9a-fA-F]{6}$/`).
- Semver: "Must be semver like '1.2.3' or '0.10.0'" (`/^\d+\.\d+\.\d+$/`).
- Cron: "Must be cron like '0 9 * * 1' (every Monday 9am)" (`/^(\S+\s){4}\S+$/`).

The error message is your teaching interface. A good example means the retry almost always succeeds. See `errors-protocol-vs-tool.md` for error shape.

<!-- src: audit-agentic-mcp/references/patterns/schema-design.md#Pattern 7: Safe Tool Name Characters Only | audit-agentic-mcp/references/patterns/schema-design.md#The Bug | audit-agentic-mcp/references/patterns/schema-design.md#Naming Convention | audit-agentic-mcp/references/patterns/schema-design.md#Lint Rule (TypeScript) -->
## Use safe tool-name characters only

Use only `[a-z0-9_]` in tool names. Slashes, hyphens, dots, spaces and non-ASCII characters have caused whole-connection failures in production MCP clients, not validation errors but silent crashes; `/` is the most dangerous because some clients parse names as URI path segments. Reported breakages by character (client names and versions: `../fresh/mcp-client-and-sdk-quirks.md`): `/`, `-`, `.`, spaces, Unicode.

Naming: dangerous `read/file`, `git-status`, `search.files`, `get_user's_data`; safe `read_file`, `git_status`, `search_files`, `get_user_data`.

Lint rule: `^[a-z][a-z0-9_]{0,63}$` (lowercase letters, digits, underscores; starts with a letter; at most 64 characters), enforced at registration with a clear error. Add the check to CI: a broken tool name can take down an entire MCP connection, not just one tool. TypeScript registration wrapper: `../frameworks/mcp-ts/schema-design-portability.md`.

<!-- src: audit-agentic-mcp/references/patterns/schema-design.md#Pattern 8: Cross-Model Portable Schema Rules | audit-agentic-mcp/references/patterns/schema-design.md#Compatibility Rules (7 Hard Rules) | audit-agentic-mcp/references/patterns/schema-design.md#Compatibility Matrix | audit-agentic-mcp/references/patterns/schema-design.md#Test Your Schema -->
## Cross-model portable schema rules

If several LLM clients (Claude, GPT-4, Gemini) reach the server, each has different JSON Schema support; a schema that works in one can fail silently in another or make a client ignore the tool. A schema that crashes one client silently drops the tool from that client's context. Build once, deploy everywhere with these seven rules:

1. **No `oneOf`/`anyOf`/`allOf` at the top of an input schema.** Pick the most permissive type and coerce server-side (`{type: "string", description: "Can also be a number (will be converted)"}`).
2. **Max 3 levels of nesting.**
3. **No `$ref`:** most clients do not resolve references in tool schemas; inline all definitions.
4. **No `format` validators beyond `date-time` and `email`:** support is inconsistent (for example `format: "uri"` is ignored by some models). Describe the format in the `description` instead.
5. **No `default` on required fields;** it confuses some implementations. Defaults only on optional fields.
6. **Inline enums up to 10 values;** above that describe the values and validate server-side. For large enums, split into a separate "mode" tool that narrows the scope.
7. **Set `additionalProperties: false`;** it helps every model see the schema is strict.

> Reconciled: the source's rule 1 banned `oneOf`/`anyOf`/`allOf` outright and its rule 6 said "under 10" while its matrix said enums above 20 degrade. This file uses: avoid `oneOf`/`anyOf` at the top of an input schema; inline enums up to 10 values. Per-model matrix and the 20-value report: `../fresh/mcp-model-behavior.md`.

> Unresolved: rule 2 allows 3 levels of nesting, while `schemas-flat-and-sized.md` says never nest 2+ levels. Treat flat (no nesting beyond one level) as the design target and 3 levels as the portability ceiling.

Test your schema with a small portability validator run in CI: flag `oneOf`/`anyOf` ("Remove oneOf/anyOf for Gemini compatibility"), `$ref` ("Inline $ref for cross-client compatibility"), nesting depth above 3 ("Nesting too deep (>3) for GPT-4 reliability"), and enums above 10 values ("Large enum (>10) degrades accuracy"). Code: `../frameworks/mcp-ts/schema-design-portability.md`.
