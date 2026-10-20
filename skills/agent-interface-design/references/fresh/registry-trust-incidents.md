---
as_of: unknown
verify_before_citing: true
---

# Named MCP trust incidents of 2025

> Read when: you assess supply-chain risk for an MCP registry, gateway, or third-party server, or need the real incidents (Smithery path traversal, postmark-mcp rug pull, CVE-2025-6514) and their lessons. Dates are as the source gave them.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#5. Named Trust Incidents (2025) -->
## Named trust incidents (2025)

The ecosystem's trust architecture is not theoretical. Three incidents in 2025 reshaped how registries and gateways approach supply-chain risk. Any brand-sensitive MCP must be designed with these in mind. Defense tactics: `mcp/security/*`.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#Incident 1 — Smithery path traversal exposed 3,000+ hosted servers -->
## Incident 1: Smithery path traversal exposed 3,000+ hosted servers

- **Timeline:** discovered 2025-06-10; disclosed and acknowledged 2025-06-13; partial fix + key rotation 2025-06-14; full fix 2025-06-15; public write-up 2025-10-15 through 2025-10-22 (blog.gitguardian.com 2025-10 "breaking-mcp-server-hosting"; scworld.com 2025-10).
- **Attack:** attacker-controlled `smithery.yaml` with `dockerBuildPath: ".."` and a malicious `Dockerfile` exfiltrated builder files including `.docker/config.json`, recovering an overprivileged fly.io token reusable against the fly.io Machines API: arbitrary code execution on any machine in the organization.
- **Impact:** thousands of API keys exposed across 3,000+ hosted apps. No evidence of exploitation; fully patched.
- **Lesson:** centralized hosting platforms are high-value targets. Multi-tenant build systems need sandboxed builders, scoped build-time credentials, and yaml-path validation that rejects `..`.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#Incident 2 — `postmark-mcp` rug pull (first in-the-wild malicious MCP) -->
## Incident 2: `postmark-mcp` rug pull (first in-the-wild malicious MCP)

- **Timeline:** 2025-09-15 npm upload by `phanpak` impersonating ActiveCampaign's official Postmark MCP; 2025-09-17 v1.0.16 silently added a BCC of every email to `phan@giftshop[.]club`; 2025-09-29 reported by The Hacker News and Koi Security; package deleted (thehackernews.com, 2025-09).
- **Downloads before discovery:** 1,643.
- **Attack class:** rug-pull (trusted version, auto-update, backdoor) plus npm typosquat against a legitimate brand.
- **Impact:** exfiltration of password resets, invoices, customer correspondence, internal memos.
- **Lesson:** the Official Registry's namespace authentication is the structural fix. Brands must claim `com.<domain>/*` via DNS verification before a squatter claims it via GitHub. This is why the "tool vendor" archetype publishes to the Official Registry first (`registry-publisher-picker.md`).

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#Incident 3 — CVE-2025-6514 `mcp-remote` RCE -->
## Incident 3: CVE-2025-6514 `mcp-remote` RCE

- **Timeline:** discovered 2025-07 by JFrog.
- **Attack:** a malicious MCP server returns a crafted `authorization_endpoint`; `mcp-remote` (no URL validation) passes it to the system shell: RCE on the MCP client (docker.com blog 2025 "mcp-horror-stories-the-supply-chain-attack"; nvd.nist.gov/vuln/detail/CVE-2025-6514).
- **Scale:** 437,000+ downloads before patch. Used in tutorials by Cloudflare, Hugging Face, Auth0.
- **Significance:** first documented full RCE against an MCP client from a supply-chain vector. Shifted the community's view: the client-side adapter is a supply-chain target.
- **Lesson:** validate every URL and every string consumed from upstream MCP responses before passing it to anything shell-like.

<!-- src: audit-agentic-mcp/references/patterns/registry-and-distribution.md#Bonus — Kaspersky `devtools-assistant` PoC rug pull (2025-09-15) -->
## Bonus: Kaspersky `devtools-assistant` PoC rug pull (2025-09-15)

Published as a benign PyPI package; later backdoored to exfiltrate files via disguised GitHub API traffic (securelist.com, 2025-09). Not weaponized in the wild, but formalizes the MCP rug-pull technique: trust, auto-update, swap.
