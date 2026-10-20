---
as_of: 2026-01-15
verify_before_citing: true
---
# MCP auth reference implementations to study

> Read when: you are about to write an MCP authorization layer and want a production- or reference-quality implementation to read first.

Verify before citing: every entry was production or reference quality as of the cited date; repositories, packages and docs move. Read one before writing your own auth layer. The rules they should satisfy: [../mcp/security/auth-audit-checklist.md](../mcp/security/auth-audit-checklist.md).

<!-- src: audit-agentic-mcp/references/patterns/auth-identity.md#16. Reference Implementations To Study -->
## Implementations

- **Stytch + Cloudflare Workers**: `github.com/stytchauth/mcp-stytch-consumer-todo-list` (2025-04-19). Clean AS separation, DCR, PKCE `S256`, PRM, per-user KV keying, `jwtVerify({ audience, issuer, typ: "JWT", algorithms: ['RS256'] })`. Blog walkthrough: https://stytch.com/blog/building-an-mcp-server-oauth-cloudflare-workers/
- **Cloudflare `workers-oauth-provider`**: `developers.cloudflare.com/agents/guides/remote-mcp-server/` plus `cloudflare/ai` PR #99 (the first public fix to the `2025-03-26` confused-deputy class; reference for the consent-cookie interrupt).
- **WorkOS mcp.shop + AuthKit**: `github.com/workos/mcp.shop` with `workos.com/docs/authkit/mcp`. FastMCP's `AuthKitProvider` auto-discovers AS endpoints and validates JWT audience. XAA / `id-jag` support for enterprise.
- **Clerk mcp-nextjs-example**: `github.com/clerk/mcp-nextjs-example` with the `mcp-handler` and `@clerk/mcp-tools` packages. PRM exposed at `/.well-known/oauth-protected-resource/mcp`; `withMcpAuth` + `verifyClerkToken`; explicit CORS on metadata endpoints; DCR opt-in from the dashboard.
- **Upstash Context7**: `@upstash/context7-mcp` (2026-01-15). End-to-end DCR + PKCE `S256`, opaque-token validation via `/oauth/userinfo`, project-selection consent step, 3-hour access token TTL.
- **Christian Posta / Solo.io "hard way"**: `github.com/christian-posta/mcp-auth-step-by-step`. Annotated Python FastAPI walkthrough of RFC 9728 + 8414 + 8707, plus scope-check dispatch.
- **localden APIM sample**: `github.com/localden/remote-auth-mcp-apim-py`. Azure API Management policies for `/register`, `/authorize`, `/token` including the consent-cookie interrupt.
- **AWS AgentCore Gateway**: policy-per-tool fine-grained access for multi-tenant MCP, Cedar-based PDP; see AWS docs for the 2025 preview.
- **Trail of Bits `mcp-context-protector`**: companion to the ETDI paper. Beta 2025-07-28. TOFU pinning of server instructions and tool descriptions, ANSI sanitization, prompt-injection guardrail. Blog: https://blog.trailofbits.com/2025/07/28/we-built-the-security-layer-mcp-always-needed/

Cross-reference: blog.modelcontextprotocol.io, first MCP anniversary (2025-11-25).
