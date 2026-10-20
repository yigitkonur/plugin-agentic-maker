---
as_of: 2026-04
verify_before_citing: true
---
# AWS Lambda limits for remote MCP servers

> Read when: you are hosting a remote MCP server on AWS Lambda, or a tool may run longer than 15 minutes.

Verify before citing: platform limits and prices change; check the vendor page.

Durable lesson: Streamable HTTP needs response streaming (Lambda Web Adapter), and the 15-minute wall means long tools must return a job id and finish elsewhere. Code is in `../frameworks/mcp-ts/deployment-platforms.md`; the generic polling design is in `../mcp/ops-long-running-tasks.md`.

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#10. AWS Lambda: Set `AWS_LWA_INVOKE_MODE=response_stream` for Streamable HTTP -->
## Response streaming with the Lambda Web Adapter

MCP's Streamable HTTP transport requires the server to stream responses. Plain Lambda function URLs buffer the full response, which is incompatible. The fix is the **Lambda Web Adapter (LWA)** with response streaming enabled.

```dockerfile
FROM public.ecr.aws/lambda/nodejs:20
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1 /lambda-adapter /opt/extensions/lambda-adapter
ENV AWS_LWA_INVOKE_MODE=response_stream
ENV AWS_LWA_ASYNC_INIT=true
ENV PORT=8080
COPY dist/ ${LAMBDA_TASK_ROOT}/
CMD ["index.handler"]
```

| Limit | Value | Consequence |
|---|---|---|
| Lambda timeout | 15 min (900s) **hard** | No override exists |
| Streamed response | 200 MB max | 6 MB buffered fallback |
| Bandwidth | Uncapped first 6 MB, then **2 MB/s** | Large blobs throttle hard |
| Init timeout | 10s default | `AWS_LWA_ASYNC_INIT=true` defers blocking work |

The Node.js **managed** runtime gained response streaming support on **2025-04-22**. Python still requires the container-image workaround.

Sources (accessed 2026-04): github.com/aws/aws-lambda-web-adapter; docs.aws.amazon.com/lambda/latest/dg/configuration-response-streaming.html; github.com/aarora79/streamable-mcp-serverless.

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#11. Lambda's 15-Minute Wall Forces SQS + Webhook for Long-Running MCP Tools -->
## SQS plus webhook for tools over 15 minutes

A tool that might take longer than 15 min (full-repo indexing, transcoding, multi-agent batch jobs) cannot run inline on Lambda. Lambda receives the `tool_call`, enqueues to SQS with a `jobId`, and returns **immediately** with `{ jobId, status: "queued" }`. A separate SQS-triggered worker (Fargate, ECS, or another Lambda) does the work and POSTs completion via webhook, or the agent polls a `get_job_status({ jobId })` tool. The queued response carries `poll_tool` and `estimated_seconds` (the example uses `get_index_status` and 180).

The MCP session never blocks on the long job. Mandatory on Lambda, useful everywhere else. See the polling-tool pattern in `../mcp/ops-long-running-tasks.md`.

Sources (accessed 2026-04): the Lambda response-streaming doc above; github.com/aarora79/streamable-mcp-serverless.
