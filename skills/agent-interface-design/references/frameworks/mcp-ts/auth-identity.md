# TypeScript: keep upstream refresh tokens in a key-value store

> Read when: you are implementing URL-mode elicitation OBO on a Workers-style runtime and need the callback and per-call refresh code.

Layout and trade-offs: [../../mcp/security/auth-multi-tenant-patterns.md](../../mcp/security/auth-multi-tenant-patterns.md).

<!-- src: audit-agentic-mcp/references/patterns/auth-identity.md#15. Multi-Tenant SaaS Reference Pattern B — URL-Mode Elicitation -->
## Store and refresh upstream tokens (Cloudflare Workers KV)

```ts
// On callback:
await env.UPSTREAM_TOKENS.put(
  `github:${mcpSub}`,
  JSON.stringify({ refresh_token, aud: "api.github.com", scopes }),
  { metadata: { createdAt: Date.now() } }
);

// On subsequent tool calls (inside the tool handler):
async function callGithub(env, mcpSub, request) {
  const raw = await env.UPSTREAM_TOKENS.get(`github:${mcpSub}`); // string | null
  if (!raw) return reauthRequired(); // no grant yet: send the user through URL-mode elicitation again
  const stored = JSON.parse(raw);
  const access = await refreshUpstream(stored.refresh_token);
  if (access.refresh_token) { // providers that rotate refresh tokens revoke the old one
    await env.UPSTREAM_TOKENS.put(`github:${mcpSub}`, JSON.stringify({ ...stored, refresh_token: access.refresh_token }));
  }
  return fetchGithub(access.access_token, request);
}
```
