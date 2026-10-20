---
as_of: 2026-04
verify_before_citing: true
---
# Smithery manifest rules for MCP servers

> Read when: you are publishing an MCP server to Smithery and a deploy fails silently or the Connect form shows the wrong fields.

Verify before citing: platform limits and prices change; check the vendor page.

Durable lesson: the runtime and the start command type must agree, and the config schema is the user-facing form, so make required fields explicit.

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#8. Smithery Requires `startCommand.type: http` for Container Deployments -->
## Runtime must match startCommand.type

Smithery is a registry, hosted gateway and CLI for MCP servers. Its `smithery.yaml` manifest distinguishes two runtimes, and mismatching `runtime` with `startCommand.type` silently fails at deploy time.

```yaml
# smithery.yaml - container runtime
runtime: container
build:
  dockerfile: Dockerfile
  dockerBuildPath: .
startCommand:
  type: http            # REQUIRED for container runtime
  configSchema:
    type: object
    required: ["TAVILY_API_KEY"]
    properties:
      TAVILY_API_KEY:
        type: string
        description: "Tavily API key from https://tavily.com"
  exampleConfig:
    TAVILY_API_KEY: "tvly-..."
```

```yaml
# smithery.yaml - stdio runtime (JS bundle only)
runtime: stdio
startCommand:
  type: stdio
  commandFunction: |-
    (config) => ({
      command: "node",
      args: ["dist/index.js"],
      env: { TAVILY_API_KEY: config.TAVILY_API_KEY }
    })
```

- `runtime: container` must use `type: http`.
- `runtime: stdio` must use `type: stdio` with a JS `commandFunction`: no Docker, no Python, no Go.

Sources (accessed 2026-04): smithery.ai/docs/build; the tavily-ai/tavily-mcp and blockscout/mcp-server smithery.yaml files.

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#9. Smithery `configSchema` Auto-Renders the Connect UI — Make Required Fields Explicit -->
## configSchema renders the Connect form

Smithery Connect reads your `configSchema` (JSON Schema Draft-7) and builds the user-facing form from it. `required` becomes required inputs, `description` becomes help text, `format: password` masks the field.

```yaml
configSchema:
  type: object
  required: ["API_KEY", "WORKSPACE_ID"]
  properties:
    API_KEY: { type: string, format: password, description: "Get your key at https://app.example.com/settings/api" }
    WORKSPACE_ID: { type: string, description: "UUID of the workspace" }
    DEBUG: { type: boolean, default: false }
```

Optional fields without `default` arrive as `undefined`, so the server must tolerate missing config. Publish with `smithery mcp publish <url> -n myorg/my-server` after `smithery auth login`.

Sources: smithery.ai/docs/build (accessed 2026-04); github.com/smithery-ai/cli v4.8.0 (2026-04-12).
