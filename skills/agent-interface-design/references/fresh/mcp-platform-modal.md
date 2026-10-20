---
as_of: 2026-04
verify_before_citing: true
---
# Modal for GPU-backed MCP servers

> Read when: you are hosting a Python or GPU-heavy MCP server on Modal.

Verify before citing: platform limits and prices change; check the vendor page.

Durable lesson: Modal containers are ephemeral, so run the server stateless; the draw is GPU pricing. Code is in `../frameworks/mcp-python/deployment-platforms.md`.

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#17. Modal MCP Servers Must Set `stateless_http=True` -->
## stateless_http and GPU pricing

Modal's serverless functions are ephemeral: containers scale to zero, scale cold, and move between hosts. Per-session Durable-Object-style state is not supported, so FastMCP must run in stateless mode (`stateless_http=True`). Stateless mode loses sampling, elicitation, progress and cancellation; see `../mcp/protocol-capability-gating.md`.

Pricing, Modal's edge being GPU economics: H100 $0.001097/sec, A10 $0.000306/sec, CPU $0.0000131/core-sec, Sandbox (code-exec) $0.00003942/core-sec. Starter tier: $30/mo free credits, 100 container / 10 GPU concurrency.

Sources (accessed 2026-04): modal.com/docs/examples/mcp_server_stateless; modal.com/pricing.
