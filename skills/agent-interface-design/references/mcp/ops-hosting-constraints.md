# Hosting constraints for remote MCP servers

> Read when: you are choosing or auditing where a remote MCP server runs and need the platform-shaped rules (state, duration, response size, scale-to-zero) before reading vendor specifics.

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#MCP Deployment Platform Patterns -->
Every hosting platform has its own quirks for session state, Streamable HTTP, request timeouts, response caps, auth primitives and cold starts, and those quirks decide whether a given MCP workload can run there at all. This file holds only the platform-shaped rules that hold across vendors. Generic transport choice is in `ops-transport-selection.md`, stdout purity in `ops-stdio-hygiene.md`, rate limiting and caching in `ops-rate-limiting-and-caching.md`, Kubernetes deployment in `ops-kubernetes.md`, and lazy auth in `ops-server-resilience.md`.

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#Cross-Cutting Decision Heuristics -->
## Cross-cutting decision heuristics

- **Scale-to-zero plus in-memory sessions is always broken.** If you want scale-to-zero, externalize session state to Redis, a key-value store, a per-session durable object or a document database, or set min-replica to 1 or more.
- **Response-size caps and request-duration limits are platform constants, not bugs.** Design tools to fit the envelope, or offload the artifact via a signed URL and let the agent poll for completion. The polling-tool design is in `ops-long-running-tasks.md#polling-tool-pattern`.
- **Session state lives in a per-session durable object or an external store.** Do not reach for a sticky load balancer if you also want autoscaling: session affinity and horizontal autoscaling fight each other.
- **Price by the dominant axis** of the workload (GPU, always-on state, bursty stateless, long single calls, regulation) rather than by compute alone.
- **Stateless hosting disables the server-to-client features.** Sampling, elicitation and progress need a session or an open stream, and cancellation only reaches the instance running the request; see `protocol-capability-gating.md`.

> Reconciled: the source pointed to `error-handling.md` for the polling-tool pattern, which has no such section; this file points to ops-long-running-tasks.md.

## Where the specifics are

Each file is time-sensitive (limits, prices, versions); verify before citing.

- Cloudflare Workers: `../fresh/mcp-platform-cloudflare.md`
- Vercel: `../fresh/mcp-platform-vercel.md`
- Smithery: `../fresh/mcp-platform-smithery.md`
- AWS Lambda: `../fresh/mcp-platform-aws-lambda.md`
- GCP Cloud Run: `../fresh/mcp-platform-gcp-cloud-run.md`
- Azure Container Apps: `../fresh/mcp-platform-azure-container-apps.md`
- Fly.io: `../fresh/mcp-platform-fly.md`
- Deno Deploy: `../fresh/mcp-platform-deno-deploy.md`
- Modal: `../fresh/mcp-platform-modal.md`
- Render, Koyeb, Northflank: `../fresh/mcp-platform-render-koyeb-northflank.md`
- Composio: `../fresh/mcp-platform-composio.md`
- Profiles, picker rubric and recommendations: `../fresh/mcp-platform-picker.md`
- Scaling decisions: `../decisions/scaling.md`
