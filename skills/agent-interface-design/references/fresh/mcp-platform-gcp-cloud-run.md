---
as_of: 2026-04
verify_before_citing: true
---
# GCP Cloud Run for remote MCP servers

> Read when: you need a managed platform for single MCP tool calls that run close to an hour, or a first Cloud Run deploy of an MCP server fails or is exposed publicly.

Verify before citing: platform limits and prices change; check the vendor page.

Durable lesson: Cloud Run has the longest managed request timeout, but you must bind `0.0.0.0` and keep authentication on. Code is in `../frameworks/mcp-python/deployment-platforms.md`.

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#12. GCP Cloud Run Has the Longest HTTP Timeout of Any Managed Platform — 60 Minutes -->
## 60-minute request timeout

Cloud Run caps request duration at 3,600 seconds (60 min), default 300s. That is 4.5x Vercel Enterprise's 800s and 4x Lambda's 900s. When you need one managed platform that can run a single MCP tool call for close to an hour, Cloud Run is the answer.

> Reconciled: the source said Cloud Run's 3,600 s limit is "double" Vercel Enterprise's 800 s; 3600/800 is 4.5x (and 4x Lambda's 900 s); this file uses 4.5x.

```bash
gcloud run deploy my-mcp \
  --source . \
  --region us-central1 \
  --timeout 3600 \
  --no-allow-unauthenticated \
  --port 8080
```

Cloud Run is stateless by default; sticky sessions require `--session-affinity` and externalized state (Firestore or Memorystore for Redis). GPU is GA for Cloud Run as of mid-2025, viable for Python/ML MCP servers that need sub-60-min wall-clock bursts.

Sources: cloud.google.com blog "build and deploy a remote MCP server to Cloud Run in under 10 minutes" (2025-06-17); cloud.google.com/run/docs/configuring/request-timeout (accessed 2026-04).

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#13. Cloud Run MCP Servers Must Bind `host="0.0.0.0"` and Use `--no-allow-unauthenticated` -->
## Bind 0.0.0.0 and keep auth on

Two Cloud Run footguns kill first-time MCP deploys:

1. Binding to `127.0.0.1`: Cloud Run routes external traffic to the container, and localhost is invisible to the proxy. Bind `0.0.0.0:${PORT}` with `PORT` from env (default 8080).
2. Leaving auth off: `--allow-unauthenticated` exposes MCP to the public internet. Use `--no-allow-unauthenticated` plus `roles/run.invoker` IAM grants.

Local testing against a protected deployment: `gcloud run services proxy my-mcp --port=8080`; the MCP client hits `localhost:8080` with local gcloud credentials.

Source: the Cloud Run blog above (2025-06-17).
