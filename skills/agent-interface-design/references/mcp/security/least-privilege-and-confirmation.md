# Limit what a tool can do: delegated tokens, annotations, confirmation

> Read when: you are choosing which credential a tool uses, which safety annotations it declares, or which operations need a human to approve them.

<!-- src: audit-agentic-mcp/references/patterns/security.md#2. Use Delegated Permissions, Not a Shared Superuser Token -->
## Use delegated permissions, not a shared superuser token

The biggest security mistake in MCP servers is a single admin API key for all operations: if a prompt injection succeeds it has full access to everything.

- Bad: one credential from the environment shared by every request; a `get_user_data(user_id)` tool can then read ANY user.
- Good: the tool uses the requesting user's delegated token, so the upstream API itself enforces access control and returns only what that user can see.

Implementation patterns:

- Entra ID / OAuth delegation: use the requesting user's OAuth token, not a service account. The underlying application's RBAC limits what can be accessed.
- Per-user JWT tokens: issue scoped tokens at session creation that encode the user's permission level.
- Row-level security: when querying a database, filter by the user's tenant/org ID at the query level.

This is the strongest defense against prompt injection. Even if an attacker tricks the model into calling tools maliciously, the damage is limited to what that specific user can already access. For obtaining upstream tokens, see `auth-obo-and-token-passthrough.md`. Code: `../../frameworks/mcp-python/security.md`.

Sources: Christian Schneider, "Securing MCP: a defense-first architecture guide".

<!-- src: audit-agentic-mcp/references/patterns/security.md#3. Use Tool Annotations to Signal Safety Properties -->
## Declare tool annotations

The MCP spec supports tool annotations that tell the agent and host about a tool's safety characteristics, enabling automatic permission decisions. Set all four on every tool:

| Annotation | Meaning for the agent |
|---|---|
| `readOnlyHint: true` | Agent may auto-approve without human confirmation, but only for a server the user trusts: the spec treats annotations from an untrusted server as untrusted claims |
| `destructiveHint: true` | Agent should require explicit human approval |
| `idempotentHint: true` | Agent knows it is safe to retry on failure |
| `openWorldHint: true` | Agent knows the tool accesses external/unbounded resources |

Example profiles: a search tool is `readOnlyHint: true`, `destructiveHint: false`, `idempotentHint: true`, `openWorldHint: false`. A permanent delete is `readOnlyHint: false`, `destructiveHint: true`, `idempotentHint: false` (cannot be undone), `openWorldHint: false`.

Not all clients respect annotations yet, but setting them is forward-compatible and documents intent for human readers. Include the annotation fields in any signed schema payload: flipping `destructiveHint` from `true` to `false` bypasses confirmation gates (see `tool-schema-integrity.md`). Code: `../../frameworks/mcp-python/security.md`.

Sources: MCP specification (Tools); Anthropic "Writing effective tools for AI agents".

<!-- src: audit-agentic-mcp/references/patterns/security.md#4. Require Human Confirmation for Destructive Operations -->
## Require human confirmation for destructive operations

Split tools into a read tier (auto-approve) and a write tier (confirm). This matters most when responses contain user-generated content that could include injection.

```
AUTO-APPROVE (read-only, trusted server only):
  - search_*, list_*, get_*, describe_*
  - Any tool with readOnlyHint: true, if the host trusts the server that set it

ALWAYS REQUIRE CONFIRMATION:
  - delete_*, remove_*, drop_*
  - send_message, post_comment, create_*
  - Any tool that modifies external state
  - Any tool that processes user-generated input
```

Server-side confirmation pattern: when an operation crosses a threshold (example: `send_bulk_email` to more than 10 recipients), return a non-error response that states what is about to happen (recipient count, subject), tells the agent to confirm with the user, and names the follow-up call (`send_bulk_email_confirmed(batch_id='...')`) that actually executes.

Escalation principle: read tools are always safe; write tools need confirmation if the data comes from external sources; delete tools always need confirmation regardless of source. Prompt injection can make the model believe a destructive action is what the user wants, and a human in the loop is the only reliable defense for irreversible operations. Code: `../../frameworks/mcp-python/security.md`.

Sources: community practitioner reports on prompt-injection-safe MCP use.
