---
as_of: 2026-02-27
verify_before_citing: true
---
# Azure Container Apps modes for MCP

> Read when: you are choosing between hosting your own MCP server on Azure Container Apps and running untrusted tool code in per-session sandboxes.

Verify before citing: platform limits and prices change; check the vendor page.

Durable lesson: keep one replica warm for interactive servers; use dynamic sessions only when tools execute untrusted or user-supplied code.

<!-- src: audit-agentic-mcp/references/patterns/deployment-platforms.md#14. Azure Container Apps Offers Two MCP Modes — Standalone and Dynamic Sessions -->
## Standalone or dynamic sessions

Azure Container Apps (ACA) has a second mode: **dynamic sessions**. Instead of hosting your MCP server, Azure runs the tool code inside Hyper-V isolated per-session sandboxes. Use it when tools need to execute untrusted or user-supplied code.

| Mode | You deploy | Per-session isolation | Use for |
|---|---|---|---|
| Standalone | Your MCP server container | No (standard ACA replicas) | Normal remote MCP |
| Dynamic sessions | The tool *code* | Yes: Hyper-V sandbox per session | Code-execution-as-a-service, untrusted workloads, multi-tenant with hard isolation |

Standalone mode uses Entra ID built-in auth. Dynamic sessions use API keys scoped per session pool.

ACA docs explicitly recommend `min-replica: 1` for interactive MCP servers: scale-to-zero cold starts (5-15s) break interactive agent loops. The `ingress.transport: auto` default upgrades to HTTP/2 when clients negotiate.

```bash
az containerapp create \
  --name my-mcp --resource-group rg \
  --image myregistry/my-mcp:latest \
  --ingress external --target-port 8080 \
  --min-replicas 1 --max-replicas 10
```

Source: learn.microsoft.com/en-us/azure/container-apps/mcp-overview (2026-02-27).
