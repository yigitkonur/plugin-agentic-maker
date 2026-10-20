---
as_of: unknown
verify_before_citing: true
---

# Freshness checklist for MCP claims

> Read when: you are about to make a version-sensitive claim about MCP SDKs, clients, pricing, CVEs, or registries and need to know what to re-verify and where to start.

<!-- src: audit-agentic-mcp/SKILL.md#Freshness checks -->
## Freshness checks

Before making version-sensitive claims, verify current MCP SDK, `mcp-use`, client compatibility, pricing, CVEs, and registry status from primary sources. Start with npm package metadata (`npm view <package> version dist-tags --json`, see `fresh/mcp-framework-picker.md`) and the official TypeScript SDK repository and release notes when framework guidance depends on SDK state.

Time-sensitive references, re-check before citing (the source's list, mapped to this corpus):

- auth and identity (OAuth profile, CIMD, OBO): `mcp/security/*`
- client compatibility: `fresh/client-compatibility.md`
- caching economics (provider prompt-cache prices and TTLs): `mcp/budget-*`, `fresh/model-behavior-cost-and-tiers.md`
- deployment platforms: `mcp/ops-*`
- model behavior: `fresh/model-behavior.md`
- registry and distribution: `fresh/registry-and-distribution.md`
- threat catalog (named attacks, dated CVEs): `mcp/security/*`

Every file in `fresh/` carries `as_of` and `verify_before_citing: true` in its front matter; when you reuse a claim, keep the vendor attribution and the date.
