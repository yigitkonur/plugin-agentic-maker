---
as_of: 2026-03
verify_before_citing: true
---
# Dated MCP auth incidents behind the attack primitives

> Read when: you need the named incident, affected versions, scores or dates behind an auth-layer attack primitive, for example to cite it in a finding.

Verify before citing: these are reports as of 2026-03, not independently re-checked. The mechanisms and defences live in [../mcp/security/auth-attack-primitives.md](../mcp/security/auth-attack-primitives.md) and [../mcp/security/auth-client-identity.md](../mcp/security/auth-client-identity.md). The wider CVE table: [mcp-cves.md](mcp-cves.md).

<!-- src: audit-agentic-mcp/references/patterns/auth-identity.md#9. Attack Primitive — DCR Rug Pull And Tool Squatting -->
## DCR abuse at scale

Cursor was publicly observed creating hundreds of thousands of DCR clients without rate limits. Sources: ETDI paper (arXiv:2506.01333, 2025-06-02); Trail of Bits, security layer MCP always needed (2025-07-28); WorkOS, DCR/MCP/OAuth (2025-12-09).

<!-- src: audit-agentic-mcp/references/patterns/auth-identity.md#10. Attack Primitive — Session Hijacking Via Unscoped Endpoints (CVE-2025-6514) -->
## Session hijack via unscoped endpoints: CVE-2025-6514

`mcp-remote` 0.0.5 through 0.1.15 interpolated a server-supplied `authorization_endpoint` into a shell, giving remote code execution on the client. 437,000+ downloads affected, CVSS 8.2. Same class: unauthenticated `/status`, `/health`, `/metrics` endpoints leaked session IDs and tenant names. Sources: https://modelcontextprotocol-security.io/known-vulnerabilities/cve-2025-6514/ ; JFrog advisory (2025).

> Unresolved: this source gives CVSS 8.2 for CVE-2025-6514, while the threat-catalog source gives 9.6 (see [mcp-cves.md](mcp-cves.md)); both are reported and neither is verified here.

<!-- src: audit-agentic-mcp/references/patterns/auth-identity.md#11. Attack Primitive — Indirect Prompt Injection To Confused Agent -->
## Indirect prompt injection to a confused agent

Invariant Labs' `ukend0464/pacman` proof of concept (2025-05-26): a malicious GitHub issue instructs the agent, via an MCP GitHub server, to pull a private repo and leak it via a pull request to a public repo. No OAuth flaw; the token was valid and scoped correctly. Sources: https://invariantlabs.ai/blog/mcp-github-vulnerability ; OWASP MCP Top 10 (MCP02-2025).

<!-- src: audit-agentic-mcp/references/patterns/auth-identity.md#12. Attack Primitive — Cross-Tenant Data Leak Via Missing Per-Agent Identity -->
## Cross-tenant leaks

Asana's MCP integration leaked cross-tenant projects and files; the bug was live 34 days. Supabase + Cursor: the MCP agent ran with the full `service_role` key, and a prompt-injected support ticket exfiltrated data via SQL, bypassing RLS because RLS was never evaluated. Sources: Raza Shariff, cross-tenant MCP exposures (2026-03); Solo.io, upstream API patterns (2025-09-17).

<!-- src: audit-agentic-mcp/references/patterns/auth-identity.md#13. Attack Primitive — Supply-Chain Backdoor In Published Servers -->
## Supply-chain backdoor

`postmark-mcp` (fake npm package) silently BCC'd outbound email. The backdoor was injected at v1.0.16 after 15 clean releases. Sources: Trail of Bits, `mcp-context-protector` beta (2025-07-28); ETDI paper (2025-06-02). Full case study: [mcp-red-team-case-studies.md](mcp-red-team-case-studies.md).
