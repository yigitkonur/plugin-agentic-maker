---
as_of: 2026-04
verify_before_citing: true
---
# Composio pricing against auth value

> Read when: you are deciding whether to buy a managed OAuth and tool-proxy service for MCP integrations or build auth yourself.

Verify before citing: platform limits and prices change; check the vendor page.

Durable lesson: price a managed auth service against the auth work it removes, not against raw compute.

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#20. Composio Isn't Free Infrastructure — Price Against the Auth Value, Not the Compute -->
## Composio pricing and the decision rule

Composio bundles an OAuth catalog, auth server and tool proxy for about 250 SaaS APIs. Pricing is per call: Free 20K/mo, Starter $29/mo for 200K, Pro $229/mo for 2M.

For 100K calls/mo, Composio is $29/mo; the same traffic on raw Lambda is about $1/mo, roughly 29x more on pure compute math. The delta buys managed OAuth for Gmail/Slack/Notion/Linear/GitHub, tool catalog and schemas, token rotation, request logging, and a shared auth UI.

Decision rule: Composio pays off when you need 5 or more third-party OAuth integrations; raw Lambda plus `workers-oauth-provider` wins for 1-2 integrations or custom auth.

Source: composio.dev/pricing (accessed 2026-04).
