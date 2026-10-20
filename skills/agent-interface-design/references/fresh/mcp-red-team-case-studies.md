---
as_of: 2025-10-10
verify_before_citing: true
---
# MCP red-team case studies and the MCPTox benchmark

> Read when: you need a real, dated incident or benchmark number to justify an MCP security control in a report.

<!-- src: audit-agentic-mcp/references/patterns/threat-catalog.md#6. Red-Team Case Studies (≥3) -->
## Case studies

Five dated studies follow (latest: 2025-10-10). Each justifies controls in `../mcp/security/threat-deep-dives.md` and `../mcp/security/threat-delivery-surfaces.md`. Verify against the primary source before citing.

<!-- src: audit-agentic-mcp/references/patterns/threat-catalog.md#6.1 WhatsApp MCP Exfiltration (Invariant Labs, 2025-04-07) -->
## WhatsApp MCP exfiltration (Invariant Labs, 2025-04-07)

Two variants both exfiltrated WhatsApp chat history:

- Sleeper rug-pull: a benign-looking MCP server was approved, then swapped its `send_message` description post-approval to shadow the WhatsApp MCP's tool and add a silent BCC on outbound messages.
- XPIA variant: a prompt-injected WhatsApp message triggered the same exfil path via `list_chats` when the agent read the inbox.

Both rely on MCP clients at the time not re-prompting on description changes and not isolating red-trust (external-data-reading) tools from blue-trust (message-sending) tools.

Sources: invariantlabs.ai/blog/whatsapp-mcp-exploited (2025-04-07); docker.com/blog/mcp-horror-stories-whatsapp-data-exfiltration-issue (2025-11-13).

<!-- src: audit-agentic-mcp/references/patterns/threat-catalog.md#6.2 GitHub MCP Private-Repo Exfiltration (Invariant, 2025-05-26) -->
## GitHub MCP private-repo exfiltration (Invariant, 2025-05-26)

A malicious issue in a public repo carried a prompt injection that hijacked the official GitHub MCP server. When the user asked Claude to triage the issue, the agent:

1. Read the attacker's issue text (XPIA vector, pattern 7).
2. Followed the embedded instruction to pull data from a private repo.
3. Opened an autonomous PR in the public repo leaking the private data.

Demo: `ukend0464/pacman` issue #1 -> PR #2. Source: invariantlabs.ai/blog/mcp-github-vulnerability (2025-05-26). Takeaway: fully qualified tool references and red/blue tool coloring would have blocked the escalation.

<!-- src: audit-agentic-mcp/references/patterns/threat-catalog.md#6.3 postmark-mcp npm Compromise (Snyk, 2025-09-25) -->
## postmark-mcp npm compromise (Snyk, 2025-09-25)

The first confirmed malicious MCP server on npm. Starting at `v1.0.16`, the package added a one-line BCC to `phan@giftshop.club` inside its `send_email` handler. The change passed code review because the diff was minimal and the package already had trusted downloads.

Sources: snyk.io/blog/malicious-mcp-server-on-npm-postmark-mcp-harvests-emails/ (2025-09-25); thehackernews.com/2025/09/first-malicious-mcp-server-found.html (2025-09-29). Takeaway: never auto-update MCP servers; pin to a commit hash; run a supply-chain scanner (CrowdStrike, Cisco, mcp-scan) against your installed set on a schedule.

<!-- src: audit-agentic-mcp/references/patterns/threat-catalog.md#6.4 Cursor MCP Config Overwrite — CVE-2025-59944 (Lakera, 2025-10-10) -->
## Cursor MCP config overwrite, CVE-2025-59944 (Lakera, 2025-10-10)

Cursor's approval check for writes to `.cursor/mcp.json` did not normalize path casing. An agent under prompt injection could write `.cUrSoR/mcp.json` or `.cursor/./mcp.json`, bypassing confirmation, silently installing new MCP servers, and achieving RCE on next run.

Source: lakera.ai/blog/cursor-vulnerability-cve-2025-59944 (2025-10-10). Takeaway: always normalize paths (case + `.` + symlinks) before running access checks.

<!-- src: audit-agentic-mcp/references/patterns/threat-catalog.md#6.5 MCPTox Benchmark (arXiv, 2025-08-19) -->
## MCPTox benchmark (arXiv, 2025-08-19)

Academic benchmark (arXiv 2508.14925): 1,312 test cases across 45 real MCP servers, 353 tools and 20 LLM agents. Key numbers:

- Top Attack Success Rate (ASR) 72.8% on o1-mini.
- Average ASR across models 36.5%.
- Parameter-tampering ASR averaged 46.7%.

Takeaway: model alignment is a weak defense. Protocol-level and client-level mitigations (TOFU, wrapper proxies, tool coloring, fully qualified references) are the reliable layer.
