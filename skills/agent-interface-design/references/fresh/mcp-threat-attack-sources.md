---
as_of: 2026-04-10
verify_before_citing: true
---
# Dated sources and incident figures for the 20-primitive attack catalog

> Read when: you need the primary source and date behind a row of the MCP attack catalog, or the dated figures that the core security files leave out.

<!-- src: audit-agentic-mcp/references/patterns/threat-catalog.md#1. Attack Catalog — 20 Named Primitives -->
## Source (YYYY-MM) per catalog row

The core catalog is `../mcp/security/threat-catalog.md`; this is its removed "Source (YYYY-MM)" column, with the CVE and version specifics of rows 15, 17, 18 and 19.

| # | Attack | Source (YYYY-MM) |
|---|---|---|
| 1 | Tool Poisoning Attack (TPA) | invariantlabs.ai 2025-04 |
| 2 | Line Jumping | Trail of Bits 2025-04-21 |
| 3 | Rug Pull | Invariant 2025-04; Semgrep 2025-09-29 |
| 4 | Cross-Server Tool Shadowing | Acuvity 2025-07-07 |
| 5 | Full-Schema Poisoning (FSP) | CyberArk 2025-05-30 |
| 6 | Advanced Tool Poisoning (ATPA) | CyberArk 2025-05-30 |
| 7 | Indirect / External Prompt Injection (XPIA) | Microsoft 2025-04-28; Marmelab 2026-02-16 |
| 8 | Covert Tool Invocation via Sampling | Unit 42 2025-12-05 |
| 9 | Conversation Hijacking via Sampling | Unit 42 2025-12-05 |
| 10 | Resource Theft / Token Consumption | Unit 42 2025-12-05 |
| 11 | Elicitation Abuse | MCP spec 2025-11-25; Semgrep 2025-09-29 |
| 12 | Confused Deputy (OAuth) | Obsidian 2026-01-29 |
| 13 | DCR Client Impersonation | MCP Blog 2025-08-22 |
| 14 | Token Passthrough / Audience Confusion | forgecode.dev 2025-07-01 |
| 15 | Predictable Session ID Hijacking | CVE-2025-6515 (JFrog 2025-10-21) |
| 16 | Supply-Chain / Typosquatting | UpGuard 2026-04-10; Snyk 2025-09-25 (postmark-mcp) |
| 17 | DNS Rebinding -> RCE (Inspector) | CVE-2025-49596 CVSS 9.4 (Oligo 2025-06-27) |
| 18 | OS Cmd Injection via OAuth Response | CVE-2025-6514 CVSS 9.6 (GHSA-6xpm-ggf7-wc3p 2025-07-09) |
| 19 | Case-Sensitivity / Path-Normalization Bypass | CVE-2025-59944 (Lakera 2025-10-10) |
| 20 | ANSI Escape / Unicode-Tag Smuggling | embracethered 2025-05-02 |

## Figures removed from the core catalog rows

- Row 16: 10-16% of servers in surveyed registries are lookalikes (UpGuard 2026-04-10).
- Row 17: precondition was "Inspector <= 0.14.0, no auth"; fix is 0.14.1; mitigation "upgrade 0.14.1; bind to loopback only; token auth".
- Row 18: mitigation "upgrade `mcp-remote` >= 0.1.16".
- Row 19: precondition "Cursor < 1.7"; mitigation "upgrade Cursor >= 1.7; normalize paths before access checks".
- Row 1 mitigation named the scanner `mcp-scan`; row 2 named the wrapper proxy `mcp-context-protector` (see `mcp-defense-tooling.md`).
- Row 13 mitigation was "CIMD (SEP-991); software statements; rate-limit DCR".

## Dates and names removed from the deep dives and supply-chain section

- TPA: Invariant Labs (2025-04-01) demonstrated the attack against Cursor and Claude Desktop; both collapsed the description in the approval UI. Wrapper proxies named: `mcp-context-protector`, Docker MCP Gateway.
- Line jumping: Trail of Bits, `blog.trailofbits.com/2025/04/21/jumping-the-line-how-mcp-servers-can-attack-you-before-you-ever-use-them/`.
- Rug pull: benign v1.0.0, then v1.0.16 mutated the description; the `postmark-mcp` compromise (Snyk 2025-09-25) is the canonical example. Scheduled scan tools: mcp-scan, CrowdStrike `mcpscanner`.
- Shadowing: Acuvity (2025-07-07) showed the attack works even when the malicious tool is never invoked.
- FSP: CyberArk (2025-05-30).
- ATPA: CyberArk (2025-05-30) named the class. Response guardrails: Invariant Guardrails, Pangea, Cisco AI Defense. MCP colors: `simonwillison.net/2025/Nov/4/mcp-colors`.
- Sampling attacks: Unit 42 (2025-12-05).
- Smuggling: `embracethered.com/blog/posts/2025/model-context-protocol-security-risks-and-exploits/` (2025-05-02).
- Defender's rule of thumb (every MCP-sourced text is user-input-equivalent): Trail of Bits 2025-07-28.
- Supply chain: `postmark-mcp` v1.0.16+ BCC'd every outbound email to an address at `giftshop[.]club`, "hundreds of weekly" downloads before discovery (Snyk 2025-09-25); UpGuard 2026-04-10 found 10-16% lookalikes; `acitons/artifact` vs `actions/artifact`; scanners to run weekly: `mcp-scan`, CrowdStrike `mcpscanner`.
