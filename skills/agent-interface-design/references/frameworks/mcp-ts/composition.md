# TypeScript composition: OpenAPI proxy, gateway config, policy gateway

> Read when: you are implementing an OpenAPI-generated MCP server, a multi-server gateway or a zero-trust policy gateway in TypeScript.

Rules and rationale: `../../mcp/ops-composition-patterns.md` and `../../mcp/ops-gateway.md`. Product names: `../../fresh/mcp-gateway-tools.md`.

<!-- src: audit-agentic-mcp/references/patterns/composition.md#5. Generate MCP Servers from OpenAPI Specs -->
## OpenAPI proxy

```typescript
import { MCPProxy } from './proxy';

// Load spec and create proxy -- each endpoint becomes a tool
export async function initProxy(specPath: string, baseUrl?: string) {
  const openApiSpec = await loadOpenApiSpec(specPath, baseUrl);
  const proxy = new MCPProxy('Notion API', openApiSpec);
  return proxy;
}

// The proxy translates MCP tool calls into HTTP requests:
// tool("createPage", { parent: {...}, properties: {...} })
//   → POST /v1/pages { parent: {...}, properties: {...} }
//   → returns structured MCP response
```

After auto-generation, override specific tools for a better model experience:

```typescript
proxy.overrideTool('search_pages', {
  description: 'Search Notion pages by title or content. Returns page IDs and titles.',
  parameters: {
    query: { type: 'string', description: 'Search text — matches titles and page content' },
    limit: { type: 'number', description: 'Max results (default: 10, max: 100)' }
  }
});
```

<!-- src: audit-agentic-mcp/references/patterns/composition.md#6. Use a Gateway/Proxy for Multi-Server Orchestration -->
## Gateway configuration

```typescript
// Gateway configuration -- declare servers, let the gateway manage lifecycle
const gateway = new MCPGateway({
  servers: [
    {
      name: 'web',
      command: 'npx',
      args: ['-y', '@anthropic/web-search-mcp'],
      lazy: true,           // only start when a tool is called
      idleTimeout: 120_000, // stop after 2min of inactivity
      healthCheck: { interval: 30_000, timeout: 5_000 }
    },
    {
      name: 'db',
      command: 'npx',
      args: ['-y', 'postgres-mcp-server'],
      lazy: true,
      idleTimeout: 300_000,
      maxRetries: 3  // circuit breaker after 3 failures
    }
  ],
  naming: 'prefixed'  // web__search, db__query — prevents collisions
});

// Client sees one server with all tools
await gateway.start();
```

<!-- src: audit-agentic-mcp/references/patterns/composition.md#7. Zero-Trust Policy Gateway -->
## Policy execution gateway

```typescript
import { createHmac } from "crypto";

interface Policy {
  allowed_tools: string[];
  per_tool: Record<string, {
    max_params?: Record<string, unknown>;
    require_context?: string[];  // Required session fields
    require_role?: string;
  }>;
}

async function loadPolicy(): Promise<Policy> {
  return JSON.parse(await fs.readFile("policy.json", "utf-8"));
}

class ExecutionGateway {
  private policy!: Policy;

  async init() { this.policy = await loadPolicy(); }

  async authorize(toolName: string, params: unknown, context: SessionContext): Promise<void> {
    if (!this.policy.allowed_tools.includes(toolName)) {
      throw new Error(`Tool "${toolName}" is not in the allowed_tools list.`);
    }

    const rule = this.policy.per_tool[toolName];
    if (rule?.require_role && context.role !== rule.require_role) {
      throw new Error(`Tool "${toolName}" requires role "${rule.require_role}". Current: "${context.role}".`);
    }
    if (rule?.require_context) {
      for (const field of rule.require_context) {
        if (!context[field]) throw new Error(`Missing required session context: ${field}`);
      }
    }
  }

  signJobTicket(toolName: string, params: unknown): string {
    const payload = JSON.stringify({ toolName, params, ts: Date.now() });
    return createHmac("sha256", process.env.GATEWAY_SECRET!).update(payload).digest("hex");
  }
}

// Wrap server dispatch
const gateway = new ExecutionGateway();
await gateway.init();

server.use(async (req, next) => {
  await gateway.authorize(req.tool, req.params, req.session);
  const ticket = gateway.signJobTicket(req.tool, req.params);
  auditLog.write({ ticket, ...req.session, tool: req.tool });
  return next();
});
```
