# MCP quick reference

> Read when: you know the symptom or the aspect of an MCP server in scope and need the one file to open first.

<!-- src: audit-agentic-mcp/SKILL.md#Quick reference card -->
## You want to... start here

| You want to... | Start here |
|---|---|
| Architect a brand-new MCP | `skills/design/references/interview-mcp.md`, then `decisions/companion-routing.md` |
| Decide MCP vs CLI vs agent skill | `decisions/mcp-vs-cli-evidence.md` |
| Evaluate tool interface quality | `mcp/design-*`, then `mcp/descriptions-*` |
| Fix schema parse failures | `mcp/schemas-*`, then `decisions/design-phase.md` |
| Improve error recovery | `decisions/error-strategy.md`, then `mcp/errors-*` |
| Harden security posture | `decisions/security-posture.md`, then `mcp/security/*` (generic defenses, then auth and identity) |
| Reduce context / token usage | `agentic-maker probe mcp "<command>"`, then `mcp/budget-*` |
| Manage 20+ tools | `decisions/tool-count.md`, then `mcp/budget-*` (progressive discovery) |
| Add sampling, elicitation, or roots | `mcp/protocol-*` |
| Pick deployment platform | `mcp/ops-*` |
| Design for a specific client | `fresh/client-compatibility.md` |
| Publish to a registry | `fresh/registry-and-distribution.md` |
| Validate with live tests | `mcp/ops-*` (testing), then a live smoke test of the running server |

<!-- src: audit-agentic-mcp/SKILL.md#Decision tree — what aspect needs attention? -->
## What aspect needs attention

```
What aspect of the MCP server is in scope?
|
+-- Brand new server, no code yet
|   +-- skills/design/references/interview-mcp.md
|   +-- decisions/companion-routing.md
|
+-- Architecture decision: should this even be an MCP server?
|   +-- decisions/mcp-vs-cli-evidence.md, decisions/mcp-vs-cli-hybrids.md
|
+-- Tool interface quality
|   +-- REST-wrapper tools ------------- mcp/design-*
|   +-- Wrong tool selected ------------ mcp/descriptions-*
|   +-- Weak next-action guidance ------ mcp/responses-*, decisions/steering-contract.md
|
+-- Input / output reliability
|   +-- Schema parse failures ---------- mcp/schemas-*
|   +-- Poor recovery errors ----------- mcp/errors-*
|   +-- Response format choice --------- decisions/response-format.md
|   +-- Error strategy choice ---------- decisions/error-strategy.md
|
+-- Security and identity
|   +-- Security posture flow ---------- decisions/security-posture.md
|   +-- Generic defenses --------------- mcp/security/*
|   +-- OAuth / CIMD / OBO ------------- mcp/security/* (auth and identity)
|   +-- Named attacks / CVEs ----------- mcp/security/* (threat catalog)
|
+-- Context, tokens, and cost
|   +-- Context budget ----------------- mcp/budget-*
|   +-- Prompt-caching economics ------- mcp/budget-*
|   +-- Tool count cliffs -------------- decisions/tool-count.md
|   +-- Progressive loading ------------ mcp/budget-*
|
+-- Protocol depth
|   +-- Sampling / elicitation / roots - mcp/protocol-*
|   +-- Resources + prompts ------------ mcp/protocol-*
|   +-- Tool response authority -------- decisions/steering-contract.md
|
+-- Client + model compatibility
|   +-- Per-client quirks -------------- fresh/client-compatibility.md
|   +-- Per-model behavior ------------- fresh/model-behavior.md
|
+-- Architecture & scaling
|   +-- Agentic workflows -------------- mcp/design-*
|   +-- Multi-server composition ------- mcp/design-*
|   +-- Growth / load distribution ----- decisions/scaling.md
|   +-- Early design decisions --------- decisions/design-phase.md
|
+-- Operations, testing, deployment
|   +-- Transport + ops ---------------- mcp/ops-*
|   +-- Hosting platforms -------------- mcp/ops-*
|   +-- Session lifecycle -------------- mcp/ops-*
|   +-- Testing strategy --------------- mcp/ops-*
|   +-- Production readiness ----------- decisions/production-readiness.md
|
+-- Distribution and trust
    +-- Vendor exemplars --------------- fresh/exemplar-servers.md
    +-- Registries / gateways ---------- fresh/registry-and-distribution.md
```
