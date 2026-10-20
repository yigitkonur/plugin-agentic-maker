# Schema versus description, server instructions and call examples

> Read when: you are deciding what goes in the schema versus the description, writing the server `instructions`, or adding correct and incorrect call examples.

Companion to `descriptions-structure-and-length.md` (structure and length budget) and `descriptions-names-and-routing.md` (names, enums, routing). Code: `../frameworks/mcp-ts/tool-descriptions.md`.

<!-- src: audit-agentic-mcp/references/patterns/tool-descriptions.md#Pattern 8: Truth in the Schema, Hints in the Description -->
## Truth in the schema, hints in the description

The schema carries machine-enforceable truth: types, required fields, enums, ranges. The description carries what the schema cannot express: side effects, auth scope, rate limits, latency, idempotency, failure modes. Do not duplicate: if the enum declares `["draft", "sent", "paid"]`, do not repeat the values; say what happens when each is picked.

Example `update_invoice_status`: description "Transition an invoice to a new status. Changing to 'sent' triggers an email to the customer (side effect, not reversible). Changing to 'paid' requires payment_id. Rate limited to 10 calls/min per invoice." Schema: required `invoice_id` ("UUID of the invoice") and `status` (enum `draft`, `sent`, `paid`, `void`); optional `payment_id` ("Required when status is 'paid'").

The description adds three things the schema cannot:
1. **Side effect:** `sent` triggers an email.
2. **Conditional requirement:** `payment_id` needed for `paid`.
3. **Rate limit:** 10 calls/min per invoice.

Anti-pattern: restating types ("invoice_id is a string") or listing enum values already in the schema; it wastes tokens and drifts when the schema changes. Principle: schema = what is valid; description = what is wise.

<!-- src: audit-agentic-mcp/references/patterns/tool-descriptions.md#Pattern 9: Use the `instructions` Field as Your Server's skills.md -->
## Use the `instructions` field as the server briefing

The MCP `initialize` response includes an `instructions` string that clients surface to the model as system-level context. It is the most reliable place to explain overall capabilities, recommended workflows and inter-tool relationships. Many clients silently ignore the spec's `prompts` feature but read `instructions` (client support: `../fresh/mcp-client-and-sdk-quirks.md`).

Write it like an `AGENTS.md`, read once at session start, with sections such as: Available Capabilities (customer CRUD + search; invoice lifecycle create -> send -> pay -> void; activity log queries), Recommended Workflows (look up a customer: `search_customers` -> `get_customer`; send an invoice: `create_invoice` -> `add_line_items` -> `send_invoice`; check payment: `get_invoice` -> `get_payment`), Important Constraints (writes need a valid session, call `authenticate` first; invoice sends are irreversible and email the customer; rate limit 60 requests/min across all tools). TypeScript form: `../frameworks/mcp-ts/tool-descriptions.md`.

Tool descriptions say what each tool does; `instructions` says how they fit together. Without it, agents discover workflows by trial and error.

<!-- src: audit-agentic-mcp/references/patterns/tool-descriptions.md#Pattern 10: Add Correct AND Incorrect Call Examples in Descriptions -->
## Show correct AND incorrect call examples

Concrete examples, happy path and common mistake, measurably improve task completion. Put them in the **parameter descriptions** of the input schema, next to the value they explain, and keep the tool description itself at about 100 tokens (never above 200; `descriptions-structure-and-length.md`). Name the return shape in one clause of the description or in the output schema (`responses-formats-and-structured.md`); do not paste an example response into the description.

```json
{"name": "search_orders",
 "description": "Search orders by customer, date range, or status. Returns up to 50 orders (id, status, total) and has_more.",
 "inputSchema": {"type": "object", "required": ["customer_id"], "properties": {
   "customer_id": {"type": "string", "description": "Customer id, e.g. cust_123."},
   "after": {"type": "string", "description": "ISO 8601 date (YYYY-MM-DD), e.g. 2024-01-01. Not 'Jan 1 2024': natural-language dates fail."},
   "before": {"type": "string", "description": "ISO 8601 date, exclusive, e.g. 2024-03-01."}}}}
```

Include: one happy-path value with realistic content; one common mistake with a brief reason it fails. Do NOT include exhaustive parameter combinations (that is the schema's job) or lengthy prose beside examples.

> Reconciled: the source put full example calls and an example response inside the description (about 150 tokens), which breaks its own 100-token target. The examples moved to the parameter descriptions and the response shape to one clause.

A single concrete example outperforms a paragraph of rules, and a wrong example inoculates against the most frequent failure mode. Response shapes: `responses-steering-and-examples.md`.
