---
as_of: 2026-03-29
verify_before_citing: true
---
# Deno Deploy sandbox rules for MCP servers

> Read when: you are deploying an MCP server to Deno Deploy and a raw socket, host binding, SSE response or auth setup fails.

Verify before citing: platform limits and prices change; check the vendor page.

Durable lesson: use TLS-aware connects, allowlist hosts, and make the server refuse to start without its auth token. Code is in `../frameworks/mcp-ts/deployment-platforms.md`.

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#16. Deno Deploy Blocks `Deno.connect` to Port 443 — Use `Deno.connectTls` -->
## Deno.connect on port 443 and other quirks

Deno Deploy's sandbox blocks raw TCP connections to port 443 to prevent unencrypted writes to what should be a TLS port. If your MCP server opens its own sockets (for example, to speak a custom wire protocol to a backend on 443), `Deno.connect` fails at runtime; use `Deno.connectTls`.

Other Deno Deploy quirks for MCP:

- **Memory cap:** 512 MB per deployment, 1 GB total across deployments on the free tier.
- **Binding `0.0.0.0`** requires `--dnsRebinding` plus an `MCP_ALLOWED_HOSTS` allowlist; wildcard `*` is rejected.
- **SSRF guard:** `Deno.connect` and `fetch()` default-block private IPs (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), localhost, and `.internal` TLDs.
- **SSE vs HTTP:** set `MCP_JSON_RESPONSE=true` to force JSON-only responses and disable SSE framing.
- **Auth:** `MCP_HTTP_BEARER_TOKEN` configures the bearer check. Set `MCP_REQUIRE_HTTP_AUTH=true` and the server refuses to start if the token env is unset, which prevents accidental public deployments.

Sources: github.com/phughesmcr/deno-mcp-template v0.7.0 (2026-03-29); docs.deno.com/deploy/pricing_and_limits (2025-10-07).
