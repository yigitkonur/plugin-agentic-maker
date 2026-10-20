---
as_of: 2026-04
verify_before_citing: true
---
# Vercel limits for remote MCP servers

> Read when: you are hosting a remote MCP server on Vercel and a long tool returns a 504, or a tool returns a large artifact and gets a 413.

Verify before citing: platform limits and prices change; check the vendor page.

Durable lesson: override the adapter's default duration, enable the platform's long-duration compute mode, and never return large artifacts through the function response; return a signed URL. Code is in `../frameworks/mcp-ts/deployment-platforms.md`.

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#6. On Vercel, Enable Fluid Compute Explicitly — Otherwise You Get 300s Max -->
## Fluid Compute and maxDuration

The `@vercel/mcp-adapter` supports both stateless and stateful (Redis-backed) MCP servers, but hits a hard wall on execution duration. The cap depends on plan and on whether Fluid Compute is enabled.

| Plan | Default max | Fluid Compute max |
|---|---|---|
| Hobby | 60s (quickstart default) | 300s |
| Pro | 60s | **800s** |
| Enterprise | 60s | **800s** |

The adapter quickstart sets `maxDuration: 60`. Long-running tools (migrations, batch jobs, AI inference chains) silently 504 with `FUNCTION_INVOCATION_TIMEOUT` unless you override it (`export const maxDuration = 800`, which requires Fluid Compute on).

Enable Fluid Compute in Project Settings -> Functions -> Fluid Compute. Without it, `maxDuration: 800` silently caps at 300s.

Sources: vercel.com/blog/building-efficient-mcp-servers (2025-06-12); vercel.com/docs/functions/limitations (2026-02-24); github.com/vercel/mcp-adapter v1.1.0 (2026-03-24).

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#7. Vercel Caps Response Bodies at 4.5 MB — Offload Large Blobs to R2/S3/Blob -->
## 4.5 MB response cap

Vercel enforces a **4.5 MB hard cap** on function response bodies. Exceeding it returns `413 FUNCTION_PAYLOAD_TOO_LARGE`. This kills any MCP tool that returns screenshots, PDF exports, parsed CSVs, or embeddings over about 300k tokens.

Fix: stream the artifact to external storage inside the tool and return a short-lived signed URL in the MCP response (for example, `Report ready: <url> (expires in 1 hour)`). Use Vercel Blob, Cloudflare R2, or S3 with 1-hour presigned URLs. Never try to chunk a 4.5+ MB response through MCP content blocks: the cap applies at the HTTP layer before MCP framing.

Source: vercel.com/docs/functions/limitations (2026-02-24).
