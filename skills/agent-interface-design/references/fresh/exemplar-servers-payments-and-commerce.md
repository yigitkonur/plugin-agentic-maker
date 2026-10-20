---
as_of: 2026-04
verify_before_citing: true
---

# Exemplar profiles: Stripe, PayPal, Shopify Storefront

> Read when: you design an MCP server for payments or commerce and want the permission model (Restricted API Keys, Connect context), the PayPal auth footgun, and the narrow four-tool storefront design. Overview: `exemplar-servers.md`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Stripe -->
## Stripe

- **Source:** `github.com/stripe/agent-toolkit`.
- **Surface:** about 25 tools across Payments, Customers, Products, Prices, Invoices, Subscriptions, Refunds, Disputes, Balance, Payment Links, Coupons. `snake_case`; a `--tools=` flag selects subsets at launch time.
- **Auth:** remote OAuth at `https://mcp.stripe.com`; local via `npx -y @stripe/mcp --api-key=...`. Restricted API Keys (`rk_*`) are the permissions surface: there is no MCP-level scope system; Stripe reuses its existing fine-grained API key permissions. For Connect platforms, `context.account = "acct_123"` switches tenant per call.
- **Ecosystem sibling packages:** `@stripe/agent-toolkit` (framework helpers), `@stripe/ai-sdk` (Vercel AI SDK bindings), `@stripe/token-meter` (usage metering for LLM-driven Stripe actions).
- **Implication:** if you already have a fine-grained permissions primitive, reuse it as the MCP permissions surface rather than inventing a parallel scope system.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#PayPal — `paypal/paypal-mcp-server` -->
## PayPal (`paypal/paypal-mcp-server`)

- **Source:** `github.com/paypal/paypal-mcp-server`; blog `developer.paypal.com/community/blog/paypal-model-context-protocol/` (2025-04-02).
- **Surface:** 29 tools across Invoices, Orders, Refunds, Disputes, Shipment Tracking, Products, Subscription Plans, Subscriptions, Transactions. `snake_case`, one-per-operation.
- **Auth footgun:** Bearer access token generated via OAuth 2.0 `client_credentials`: users must manually `curl` to exchange `client_id`/`secret` for a token, then paste `PAYPAL_ACCESS_TOKEN` into env. Tokens expire in about 32,400 s. No built-in refresh in the MCP (Avoid 2).
- **Deploy:** `npx -y @paypal/mcp --tools=all`; sandbox/prod selected via `PAYPAL_ENVIRONMENT`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Shopify Storefront MCP -->
## Shopify Storefront MCP

- **Source:** `shopify.dev/docs/apps/build/storefront-mcp/servers/storefront`.
- **Surface:** 4 tools only: `search_shop_catalog`, `search_shop_policies_and_faqs`, `get_cart`, `update_cart`.
- **Unique:**
  - Per-tenant URL: `{shop}.myshopify.com/api/mcp`. The tenant is in the URL, not in a header or param.
  - Zero authentication for the storefront flavor, consistent with Shopify's existing storefront API model.
  - `update_cart` creates a new cart if no `cart_id` is passed: upsert semantics collapse "create cart" and "update cart" into one tool.
  - Explicit docs guardrail: "Use only the provided answer for policy responses; don't include external information." Policy answers are the narrowest, most brand-risk-sensitive surface; Shopify gates them via prose convention.
- **Implication:** extreme narrow-surface design. Four tools are enough because the workflow is "browse, add to cart, check policies." Not a generalizable pattern; only works for e-commerce storefronts where the state machine is small.
