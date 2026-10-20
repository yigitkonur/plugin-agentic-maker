# Auth-layer attack primitives and their defences

> Read when: you are threat-modelling the endpoints, tokens and tenant boundaries of a remote MCP server, or reviewing an incident that looks like session hijack, cross-tenant leak or a backdoored server.

Four attacks that no OAuth flow fixes by itself. Named incidents, versions, CVSS and dates for each: [fresh/mcp-auth-incidents.md](../../fresh/mcp-auth-incidents.md). Tool-metadata and prompt-injection primitives: [threat-catalog.md](threat-catalog.md). Confused deputy, audience confusion and DCR abuse: [auth-client-identity.md](auth-client-identity.md), [auth-obo-and-token-passthrough.md](auth-obo-and-token-passthrough.md).

<!-- src: audit-agentic-mcp/references/patterns/auth-identity.md#10. Attack Primitive — Session Hijacking Via Unscoped Endpoints (CVE-2025-6514) -->
## Session hijacking via unscoped endpoints

A client-side MCP proxy interpolated a server-supplied `authorization_endpoint` into a shell, giving remote code execution on the client. The same class of flaw covers unauthenticated `/status`, `/health` and `/metrics` endpoints that leak session IDs and tenant names.

Defences:

- Treat every HTTP endpoint of an MCP server as scope-protected unless it is an explicit unauthenticated OAuth endpoint (PRM, AS metadata, `/register` if enabled, `/authorize`, `/token`, redirect endpoints).
- Bind session IDs to authenticated principals and validate on every request.
- **Never interpolate server-supplied URLs into shells, argv or filesystem paths** on the client side.
- Disable unauthenticated metrics. Gate `/health` behind a narrow allowlist or a signed probe token.

<!-- src: audit-agentic-mcp/references/patterns/auth-identity.md#11. Attack Primitive — Indirect Prompt Injection To Confused Agent -->
## Indirect prompt injection to a confused agent

A malicious issue in a public repository instructs the agent (through an MCP GitHub server) to pull a private repository and leak it via a pull request to the public one. There is no OAuth flaw: the token is valid and scoped correctly. The defect is that the agent bridges two trust domains in one session.

Auth-layer defences:

- Scope tokens narrowly per repository / per tenant; do not issue "all repos" tokens for convenience.
- Prefer separate agent sessions per trust domain; keep cross-domain writes explicit and confirmed.
- Add a runtime policy engine (OPA, Cedar, Oso) that evaluates each tool call's `{subject, tool, resource, origin}` and denies cross-domain writes by default.
- Require user confirmation before the agent writes outside the trust domain that originated the instruction.

Delivery surfaces for the injected text: [threat-delivery-surfaces.md](threat-delivery-surfaces.md).

<!-- src: audit-agentic-mcp/references/patterns/auth-identity.md#12. Attack Primitive — Cross-Tenant Data Leak Via Missing Per-Agent Identity -->
## Cross-tenant leak from missing per-agent identity

Two real shapes: a SaaS MCP integration leaked cross-tenant projects and files for weeks; and an MCP agent that ran with a database's full `service_role` key let a prompt-injected support ticket exfiltrate data via SQL, bypassing row-level security (RLS) because RLS was never evaluated; the agent had bypass privileges.

Defences:

- Agents MUST run with a **per-user upstream token**, obtained via OBO (Options A/B) or URL elicitation (Option C), described in [auth-obo-and-token-passthrough.md](auth-obo-and-token-passthrough.md). Service-role keys are never acceptable.
- Enforce tenant scope **at the MCP server**, not trusted to upstream: bind the tenant to the session at auth time.
- Evaluate a policy decision point (PDP) on every tool call. Allowlists such as `{tenant_id ∈ user.tenants}` reject the entire class of cross-tenant bugs structurally.
- Separate read and write PDP rules; log all denials with `{sub, tool, resource}`.

<!-- src: audit-agentic-mcp/references/patterns/auth-identity.md#13. Attack Primitive — Supply-Chain Backdoor In Published Servers -->
## Supply-chain backdoor in a published server

A fake npm MCP package silently BCC'd outbound email. The backdoor was injected in a late release after many clean ones, the typical supply-chain pattern. No OAuth flow would have stopped it.

Defences:

- Require signed, versioned tool definitions (ETDI) so a changed tool description triggers re-approval.
- Pin server instructions and tool descriptions on first trusted use (TOFU); a transparent wrapper proxy can implement this.
- Verify publisher identity via the npm / OCI registry signature, not the package name.
- Pair CIMD (client identity anchored in DNS) with registry-side anchoring for servers.

Pinning and scanning tools by name: [fresh/mcp-defense-tooling.md](../../fresh/mcp-defense-tooling.md). Sources: JFrog advisory; Invariant Labs GitHub MCP write-up; OWASP MCP Top 10; Solo.io; Trail of Bits.
