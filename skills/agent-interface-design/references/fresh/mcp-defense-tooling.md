---
as_of: 2026-02
verify_before_citing: true
---
# MCP defense tooling: scanners, guardrails and wrapper proxies

> Read when: you need to name a scanner, runtime guardrail or wrapper proxy for MCP security work and want to know what each detects.

<!-- src: audit-agentic-mcp/references/patterns/threat-catalog.md#4. Defense Tooling Ecosystem (≥8 named tools) -->
## Defense tooling ecosystem

Names, URLs and "first seen" dates are as the source reported them (latest: 2026-02). Check that each project still exists and is maintained.

| Tool | URL | What it detects | Maintainer | First seen |
|---|---|---|---|---|
| MCP-Scan (Invariant) | github.com/invariantlabs-ai/mcp-scan | TPA, rug pulls, cross-origin escalation, prompt injection, toxic flows | Invariant Labs | 2025-04-11 |
| Invariant Guardrails | invariantlabs.ai/guardrails | Runtime contextual security for agent flows | Invariant Labs | 2025 |
| CrowdStrike `mcpscanner` | github.com/CrowdStrike/mcpscanner | Malicious tools, prompt patterns, similarity clustering | CrowdStrike | 2025-12-18 |
| Pangea `mcpscanner` | github.com/pangeacyber/mcpscanner | MCP server/tool/resource malicious-entity detection | Pangea | 2025-11-18 |
| Cisco AI Defense `mcp-scanner` | github.com/cisco-ai-defense/mcp-scanner | Malicious tools, vulnerable Python deps, malware, behavioral issues, prompt-defense gaps | Cisco AI Defense | 2025 |
| SlowMist MCP-Security-Checklist | github.com/slowmist/MCP-Security-Checklist | Reviewer checklist (not a scanner) | SlowMist | 2025 |
| `mcpserver-audit` | github.com/ModelContextProtocol-Security/mcpserver-audit | Publishes findings to a shared audit-db + vulnerability-db | MCP-Security org | 2025 |
| `mcp-context-protector` | blog.trailofbits.com/2025/07/28/we-built-the-security-layer-mcp-always-needed | Wrapper proxy: TOFU pinning, guardrail scanning, manual change approval | Trail of Bits | 2025-07-28 |
| marmelab `mcp-vulnerability` | github.com/marmelab/mcp-vulnerability | POC for tool prompt injection, cross-tool hijack, exfil target | Marmelab | 2026-02 |
| Docker MCP Gateway / MCP Defender | docker.com/blog/mcp-horror-stories-whatsapp-data-exfiltration-issue | Description validation, signatures, LLM analysis, network isolation, audit logging | Docker | 2025-11-13 |

How to combine: pair a build-time scanner (mcp-scan, CrowdStrike, Cisco, Pangea) with a runtime wrapper (mcp-context-protector, Docker MCP Gateway, Invariant Guardrails). Scanners surface known-bad patterns; wrappers enforce TOFU pinning and manual approval on description changes, which is the only reliable defense against rug pulls.

Controls these tools implement: `../mcp/security/threat-deep-dives.md`, `../mcp/security/threat-audit-checklist.md`.
