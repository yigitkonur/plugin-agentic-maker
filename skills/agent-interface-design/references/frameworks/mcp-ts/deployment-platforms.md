# TypeScript code for remote MCP hosting platforms

> Read when: you are writing TypeScript for an MCP server on Cloudflare Workers, Vercel, Lambda, Deno Deploy or Koyeb/Northflank.

Platform facts, limits and versions are in the fresh files linked per section; verify before citing.

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#1. On Cloudflare Workers, Use `McpAgent` for Stateful, `createMcpHandler` for Stateless -->
## McpAgent on Cloudflare Workers

Facts: `../../fresh/mcp-platform-cloudflare.md`.

```typescript
import { McpAgent } from "agents/mcp";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

export class MyMCP extends McpAgent<Env, State> {
  server = new McpServer({ name: "my-mcp", version: "1.0.0" });

  async init() {
    this.server.tool("ping", {}, async () => ({
      content: [{ type: "text", text: `pong ${this.state.counter ?? 0}` }],
    }));
  }
}

export default {
  fetch(req: Request, env: Env, ctx: ExecutionContext) {
    return MyMCP.serve("/mcp").fetch(req, env, ctx);
  },
};
```

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#2. Use Durable Object WebSocket Hibernation to Stop Paying for Idle MCP Sessions -->
## WebSocket hibernation

```typescript
import { DurableObject } from "cloudflare:workers";

export class MyMCP extends DurableObject<Env> {
  async fetch(req: Request) {
    const [client, server] = Object.values(new WebSocketPair());
    // Opt the WS into hibernation instead of using addEventListener("message")
    this.ctx.acceptWebSocket(server, ["session-tag"]);
    server.serializeAttachment({ clientId: "abc", scopes: ["read", "write"] });
    return new Response(null, { status: 101, webSocket: client });
  }

  async webSocketMessage(ws: WebSocket, msg: string) {
    const state = ws.deserializeAttachment(); // Restored after rehydration
    // handle MCP frame...
  }
}
```

Keep the attachment under 2,048 bytes; larger state goes in `this.ctx.storage.sql`.

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#4. For Regulated Workloads on Cloudflare, Bind the McpAgent to the FedRAMP Jurisdiction -->
## Jurisdiction-bound Durable Object

```typescript
// Code - FedRAMP namespaces never cross into non-FedRAMP regions
const id = env.MCP_OBJECT.jurisdiction("fedramp").idFromName(userId);
```

The matching `[[durable_objects.bindings]]` block is in the fresh file.

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#5. Wrap McpAgent in `workers-oauth-provider` for Full OAuth 2.1 Without a Separate Auth Server -->
## workers-oauth-provider wrapper

```typescript
import OAuthProvider from "@cloudflare/workers-oauth-provider";

export default new OAuthProvider({
  apiRoute: "/mcp",
  apiHandler: MyMCP.serve("/mcp"),
  defaultHandler: authUiHandler,        // login page, consent screen
  authorizeEndpoint: "/authorize",
  tokenEndpoint: "/token",
  clientRegistrationEndpoint: "/register",
  resourceMetadata: { resource: "https://mcp.example.com/mcp" }, // required since workers-oauth-provider 1.x; RFC 9728 metadata for /.well-known/oauth-protected-resource
  tokenExchangeCallback: async (options) => {
    // Federate to GitHub/Google/Slack/Stytch/Auth0/WorkOS/Cloudflare Access
    const upstream = await exchangeWithUpstream(options); // verify option names against the installed version
    return { newProps: { ...options.props, upstream }, accessTokenTTL: 3600 };
  },
});
```

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#6. On Vercel, Enable Fluid Compute Explicitly — Otherwise You Get 300s Max -->
## Vercel route with maxDuration

Facts: `../../fresh/mcp-platform-vercel.md`.

```typescript
// app/api/[transport]/route.ts
import { createMcpHandler } from "mcp-handler"; // formerly @vercel/mcp-adapter

const handler = createMcpHandler((server) => {
  // register tools on `server` here
});

export const maxDuration = 800; // Override quickstart default - requires Fluid Compute ON
export { handler as GET, handler as POST };
```

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#7. Vercel Caps Response Bodies at 4.5 MB — Offload Large Blobs to R2/S3/Blob -->
## Offload a large artifact to blob storage

```typescript
import { z } from "zod";
import { put } from "@vercel/blob";
import { nanoid } from "nanoid";

server.tool("export_report", { format: z.enum(["pdf", "csv"]) }, async ({ format }) => {
  const blob = await renderReport(format);             // could be 50 MB
  const { url } = await put(`reports/${nanoid()}.${format}`, blob, {
    access: "public",
    token: process.env.BLOB_READ_WRITE_TOKEN,
  });
  return {
    content: [{ type: "text", text: `Report ready: ${url}` }],
  };
});
```

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#11. Lambda's 15-Minute Wall Forces SQS + Webhook for Long-Running MCP Tools -->
## Enqueue a long job from Lambda

Facts: `../../fresh/mcp-platform-aws-lambda.md`.

```typescript
import { z } from "zod";
import { SQSClient, SendMessageCommand } from "@aws-sdk/client-sqs";

const sqs = new SQSClient({});

server.tool("index_repository", { repo_url: z.string() }, async ({ repo_url }) => {
  const jobId = crypto.randomUUID();
  await sqs.send(new SendMessageCommand({
    QueueUrl: process.env.INDEX_QUEUE,
    MessageBody: JSON.stringify({ jobId, repo_url }),
  }));
  return { content: [{ type: "text", text: JSON.stringify({
    jobId, status: "queued", poll_tool: "get_index_status", estimated_seconds: 180,
  })}] };
});
```

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#16. Deno Deploy Blocks `Deno.connect` to Port 443 — Use `Deno.connectTls` -->
## Deno.connectTls

Facts: `../../fresh/mcp-platform-deno-deploy.md`.

```typescript
// Fails on Deno Deploy
const conn = await Deno.connect({ hostname: "api.example.com", port: 443 });

// Works
const conn = await Deno.connectTls({ hostname: "api.example.com", port: 443 });
```

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#19. Koyeb & Northflank: Scale-to-Zero Remote MCP with `sessionIdGenerator: undefined` -->
## Stateless Streamable HTTP transport

Facts: `../../fresh/mcp-platform-render-koyeb-northflank.md`.

```typescript
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
const transport = new StreamableHTTPServerTransport({
  sessionIdGenerator: undefined,   // Stateless - no server-issued session IDs
});
await server.connect(transport);
```
