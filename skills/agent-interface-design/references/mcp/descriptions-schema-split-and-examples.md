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

Concrete examples, happy path and common mistake, measurably improve task completion. Keep to one correct example and one edge case or mistake; more bloats the prompt. Include one example response so the agent can plan downstream calls without a dummy request.

```json
{"name": "search_orders",
 "description": "Search orders by customer, date range, or status. Returns max 50 results.\n\nExample — search by date range:\n{\"customer_id\": \"cust_123\", \"after\": \"2024-01-01\", \"before\": \"2024-03-01\"}\n\nExample — common mistake (wrong date format):\n{\"customer_id\": \"cust_123\", \"after\": \"Jan 1 2024\"}\nDates must be ISO 8601 (YYYY-MM-DD). Natural language dates will fail.\n\nExample response:\n{\"orders\": [{\"id\": \"ord_456\", \"status\": \"shipped\", \"total\": 99.50}], \"has_more\": true}"}
```

Include: one happy-path call with realistic values; one common mistake with a brief reason it fails; one example response showing the return shape. Do NOT include exhaustive parameter combinations (that is the schema's job) or lengthy prose beside examples.

> Reconciled: this example is far above the 100-token target; per the length rule in `descriptions-structure-and-length.md`, keep the tool description within 100 tokens (never above 200) and move the example calls into the relevant parameter descriptions of the input schema.

A single concrete example outperforms a paragraph of rules, and a wrong example inoculates against the most frequent failure mode. Response examples in descriptions: `responses-steering-and-examples.md`.
