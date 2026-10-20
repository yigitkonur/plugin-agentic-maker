---
as_of: 2025-10-21
verify_before_citing: true
---
# MCP CVEs: affected versions, dates and fixes

> Read when: you are checking whether an installed MCP component is affected by a known CVE, or citing one in a finding.

<!-- src: audit-agentic-mcp/references/patterns/threat-catalog.md#5. CVE List (≥5 dated) -->
## CVE list

The source lists these as dated entries (latest date in the list: 2025-10-21). Verify each against the advisory before citing.

| CVE | Component | Severity | Date | Impact | Fix |
|---|---|---|---|---|---|
| CVE-2025-49596 | MCP Inspector < 0.14.1 | CVSS 9.4 (Critical) | 2025-06-13 disclosed; 2025-06-27 writeup (Oligo) | CSRF + DNS rebinding -> RCE on developer workstation | Upgrade to 0.14.1+; bind to loopback; require token auth |
| CVE-2025-6514 (GHSA-6xpm-ggf7-wc3p) | `mcp-remote` < 0.1.16 | CVSS 9.6 (Critical) | 2025-07-09 | OS command injection via malicious `authorization_endpoint` | Upgrade `mcp-remote` >= 0.1.16 |
| CVE-2025-5277 | `aws-mcp-server` | n/a | 2025-05-28 | Prompt-driven command injection on host | Vendor patch; isolate in sandbox |
| CVE-2025-6515 | `oatpp-mcp` | n/a | 2025-10-21 (JFrog) | Predictable (pointer-based) session IDs -> session hijack over SSE | Replace with CSPRNG; bind session to identity; rotate |
| CVE-2025-59944 | Cursor < 1.7 | n/a | 2025-09-29 patch; 2025-10-10 writeup (Lakera) | Case-sensitivity / path-normalization bypass -> silent MCP config overwrite -> auto-RCE | Upgrade Cursor >= 1.7 |
| *(no CVE)* | `postmark-mcp` npm | n/a | malicious upload 2025-09-15; disclosed 2025-09-29 | v1.0.16+ silently BCC'd every email to `giftshop.club`; hundreds of weekly downloads | Remove; pin to a verified registry version |

> Unresolved: the threat catalog says CVSS 9.6 for CVE-2025-6514; the auth source says 8.2 (see mcp-auth-incidents.md); both are reported, neither verified here.

## Catalog rows that cite these CVEs

Rows in `../mcp/security/threat-catalog.md`: row 15 (predictable session IDs: CVE-2025-6515); row 17 (Inspector DNS rebinding: precondition "Inspector <= 0.14.0, no auth"; exploit rebinds `0.0.0.0:6277`; fix 0.14.1; CVE-2025-49596, CVSS 9.4); row 18 (`mcp-remote` command injection: CVE-2025-6514, CVSS 9.6, fix `mcp-remote` >= 0.1.16); row 19 (path-normalization bypass: Cursor < 1.7, fix Cursor >= 1.7, CVE-2025-59944). Dated sources per row: `mcp-threat-attack-sources.md`. Incident writeups: `mcp-red-team-case-studies.md`. Auth-side incident figures: `mcp-auth-incidents.md`.
