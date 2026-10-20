---
as_of: 2026-04
verify_before_citing: true
---
# Picking a platform for a remote MCP workload

> Read when: you must choose where to host a remote MCP server, or compare platform limits side by side.

Verify before citing: platform limits and prices change; check the vendor page.

Durable lesson: choose by the dominant axis of the workload (state, duration, GPU, isolation, marketplace reach), then check the per-platform file for the limits. Generic constraints are in `../mcp/ops-hosting-constraints.md`; scaling decisions in `../decisions/scaling.md`.

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#Platform Profiles (Compact Reference) -->
## Platform profiles

| Platform | Session primitive | Streamable HTTP | Max duration | Response cap | Auth | Best for |
|---|---|---|---|---|---|---|
| **Cloudflare Workers + McpAgent** | Durable Object per session + SQLite + hibernation | Native via `MyMCP.serve()` | 5 min CPU opt-in; no wall-clock limit | 100 MB (Free/Pro), 500 MB (Ent) | `workers-oauth-provider` (OAuth 2.1 + DCR) | Multi-tenant SaaS, personal CLI |
| **Vercel Fluid Compute** | BYO (Redis for resumability) | Native via `@vercel/mcp-adapter` | 300s Hobby / 800s Pro+Ent (Fluid on) | **4.5 MB hard** | BYO middleware | Team B2B, serverless-first |
| **Smithery.ai** | Managed per-server | Native when `type: http` | Container runtime limits | Container runtime limits | `configSchema` + Smithery Connect | Marketplace / public servers |
| **Modal** | None (stateless only) | Via FastMCP `streamable_http_app()` + FastAPI | Function `timeout` param | Function memory | BYO | Python/ML, GPU workloads |
| **Fly.io Machines** | Machine-local volumes | Native; machine-level | No enforced HTTP timeout | No enforced cap | `fly mcp launch` bearer token | Stateful team-internal |
| **Railway** | Service volume, 1 replica default | Native | No hard HTTP cap | Build 10 min Free / 20 min Trial | BYO | Prototypes, budget-constrained |
| **Render** | Persistent disk per service | Native | No hard cap | No hard cap | BYO (Render MCP key = account-wide) | Simple web-service MCP |
| **AWS Lambda + LWA** | None inline; SQS + webhook for long | `AWS_LWA_INVOKE_MODE=response_stream` | **15 min hard** | 200 MB streamed / 6 MB buffered; 2 MB/s past 6 MB | Cognito + JWT authorizer | Enterprise VPC, event-driven |
| **Azure Container Apps** | Standalone + Dynamic Sessions (Hyper-V) | Native (ingress `transport: auto`) | No hard cap | No hard cap | Entra ID built-in | Regulated enterprise, code-exec tools |
| **GCP Cloud Run** | Session affinity flag; state externalized | Native | **60 min (3600s)** | No hard cap | `--no-allow-unauthenticated` + IAM | Long-running single-call tools |
| **Deno Deploy** | Deno KV + event store | Via `MCP_JSON_RESPONSE=true` | Deploy-tier dependent | 512 MB mem / 1 GB deploy | `MCP_HTTP_BEARER_TOKEN` | TypeScript-native, KV-backed |
| **Koyeb / Northflank** | Scale-to-zero stateless | Native; `sessionIdGenerator: undefined` | No hard cap | No hard cap | BYO | Scale-to-zero remote MCP |

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#Picker Rubric: Workload → Platform -->
## Picker rubric

Scores are 0-10 for the specified workload. **Bold** marks the top pick(s) for the row.

| Workload | CF Workers | Vercel | Smithery | Modal | Fly | Railway | Render | Lambda | ACA | Cloud Run | Deno |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Personal CLI tool | **10** | 7 | 8 | 6 | 7 | 7 | 7 | 5 | 5 | 7 | 8 |
| Team B2B internal | **9** | 8 | 7 | 6 | **9** | 8 | 7 | 7 | 8 | 8 | 7 |
| Multi-tenant SaaS | **10** | 8 | 6 | 5 | 8 | 6 | 6 | 8 | **9** | 8 | 6 |
| Marketplace / public | 8 | 7 | **10** | 6 | 7 | 6 | 6 | 6 | 6 | 7 | 6 |
| Regulated enterprise | **9** (FedRAMP DO) | 7 | 4 | 5 | 7 | 5 | 5 | **9** (VPC) | **10** (Entra + Hyper-V) | 8 | 5 |
| GPU / ML-heavy | 4 | 5 | 3 | **10** | 7 | 6 | 6 | 7 | 7 | 8 | 3 |
| Long-running (>5 min) | 7 | 7 | 4 | 8 | **9** (no cap) | 7 | 7 | 6 | 8 | **10** (60 min) | 5 |

Headline recommendations:

| Workload | Primary | Why | Backup |
|---|---|---|---|
| Personal CLI | Cloudflare Workers + McpAgent | Free DO tier (100K req/day), built-in OAuth, hibernation ~ $0 idle | Deno Deploy |
| Team B2B internal | Cloudflare Workers **or** Fly Machines | Workers for stateless/light; Fly for stateful/container-heavy | Railway |
| Multi-tenant SaaS | Cloudflare Workers McpAgent | Per-session DO + SQLite + hibernation maps 1:1 to MCP session | Azure ACA |
| Marketplace / public | Smithery.ai container runtime | Purpose-built hosting + discovery + OAuth/configSchema | CF Workers + custom domain |
| Regulated enterprise | Azure ACA **or** CF Workers `jurisdiction: "fedramp"` | Entra ID + Hyper-V isolation; CF has FedRAMP DOs | AWS Lambda in VPC |
| Python / ML GPU | Modal | Serverless GPU at $0.001097/sec H100; native FastMCP example | Cloud Run GPU |
| Long-running (>5 min) | GCP Cloud Run | 60-minute HTTP timeout, highest of any managed platform | Fly Machines (no enforced cap) |

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#Cross-Cutting Decision Heuristics -->
## Vendor-specific heuristics

- **OAuth 2.1 is cheap on Cloudflare, expensive everywhere else.** `workers-oauth-provider` is the only first-party, DCR-capable, PKCE-capable OAuth server bundled with the runtime. On Vercel, Lambda and Cloud Run you wire Clerk, Auth0, Stytch or WorkOS by hand.
- **Price by dominant axis.** GPU workloads: Modal wins by a wide margin. Always-on stateful: Fly. Bursty stateless: Cloudflare/Vercel. Long single tool calls: Cloud Run. Regulated: ACA or CF FedRAMP.
- Platform constants behind the generic rules: Vercel 4.5 MB response cap and Lambda 15-minute timeout (see `mcp-platform-vercel.md`, `mcp-platform-aws-lambda.md`); scale-to-zero platforms where in-memory sessions break: Fly, Koyeb, Cloud Run, ACA; session affinity vs autoscaling conflicts on Cloud Run, ACA and Fly.
