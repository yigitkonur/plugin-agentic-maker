# Surface Choice: CLI, MCP, Skill or Hybrid

> Read when: you must decide whether an agent workflow should stay CLI-first, move to an MCP server, be covered by a skill, or split across surfaces.

Dated benchmark numbers, community reports and doc links: `../fresh/mcp-vs-cli-decision-dated.md`. Evidence discussion: `mcp-vs-cli-evidence.md`. Optional companion skills for building or testing MCP servers: `companion-routing.md`. This file makes the surface decision; for a CLI, `../cli/checks.md` applies next.

<!-- src: audit-agentic-cli/references/mcp-vs-cli-decision.md#1. Recommended Default -->
## Recommended default

Start with a CLI when all of these are true:

- a mature CLI already exists;
- the workflow is mostly stateless and command-shaped;
- the agent can rely on machine-readable output, semantic exit codes and non-interactive flags;
- the operator is a developer or a trusted local runtime.

Promote the workflow to MCP when any of these become dominant:

- per-user OAuth, tenant isolation, revocation, approvals or audit trails;
- no credible CLI exists, or shell parsing would be a poor fit;
- the agent needs typed discovery across many remote capabilities;
- the tool surface is stateful across calls.

Use a hybrid when:

- MCP should own auth, approvals or discovery, but execution can stay in the CLI;
- read and batch-transform steps are cheap in the CLI, but write steps need governed remote access;
- you need both a developer-friendly operator surface and a governed agent-facing surface.

Skills are a fourth option. If the agent mainly needs workflow guidance for existing tools, add a skill and keep the runtime surface as a CLI.

<!-- src: audit-agentic-cli/references/mcp-vs-cli-decision.md#3. Fast Decision Matrix -->
## Fast decision matrix

| Question | Preferred surface | Why |
|---|---|---|
| Is there already a good first-party CLI with JSON output and non-interactive flags? | CLI | Lower token cost, simpler debugging, better model familiarity. |
| Is the workflow mostly one-shot or stateless? | CLI | Process execution is enough; a protocol adds overhead without much benefit. |
| Does the workflow need per-user auth, tenant isolation, approval, or revocation? | MCP | Those are protocol and gateway problems, not shell ergonomics problems. |
| Does the tool keep state across calls: browser sessions, transactions, remote cursors? | MCP | Session continuity is native to MCP-style tool interfaces. |
| Does the agent only need instructions for how to use existing CLIs and APIs? | Skill + CLI | This is workflow knowledge, not a new runtime protocol. |
| Is governed discovery needed with cheap execution? | Hybrid | Use MCP for control plane, CLI for execution plane. |

<!-- src: audit-agentic-cli/references/mcp-vs-cli-decision.md#4. When To Stay CLI-First -->
## When to stay CLI-first

Choose a CLI when most of the value comes from process execution and command composition.

Strong signals:

- the service already has a mature CLI such as `gh`, `kubectl`, `aws`, `docker`, `git`, `jq`, `stripe` or `vercel`;
- the workflow is local, developer-facing and single-tenant;
- the model can work from a known command vocabulary plus `--help`;
- shell composition, files, pipes and redirects are central to the job;
- the data path is short enough that plain JSON output is sufficient.

Especially strong for: coding agents operating in repos; CI and automation jobs; one-shot read and mutate operations; batch transforms where the model reasons once and the shell does the work.

Do not call the CLI path "done" unless it has:

- pure machine output on stdout;
- progress and operator noise on stderr;
- semantic exit codes;
- non-interactive flags such as `--yes`, `--no-input` or `--output json`;
- deterministic auth handling for headless runs.

If those are missing, fix the CLI before treating architecture as the problem.

<!-- src: audit-agentic-cli/references/mcp-vs-cli-decision.md#5. When MCP Is The Better Abstraction -->
## When MCP is the better abstraction

Choose MCP when the value comes from governed access, typed discovery or durable state.

Strong signals:

- users connect their own accounts and permissions through OAuth;
- the system is multi-tenant and actions happen on behalf of different users;
- multiple clients or models need the same tool surface;
- the agent needs discoverable schemas rather than shell-oriented affordances;
- the tool keeps state across calls, or the workflow spans approvals and long-lived sessions;
- there is no strong CLI equivalent and a shell wrapper would mostly reimplement a remote API.

Especially strong for: enterprise SaaS integrations; customer-facing tools with scoped access; browser or session-driven automation; remote connectors reused across products and agent runtimes.

MCP is a poor fit when:

- the server mostly shells out to an existing CLI without adding meaningful auth or discovery value;
- the server mirrors dozens of thin REST endpoints directly into tools;
- the users are developers who already live in a terminal and do not need a mediated remote surface.

<!-- src: audit-agentic-cli/references/mcp-vs-cli-decision.md#6. When A Hybrid Beats Either Extreme -->
## When a hybrid beats either extreme

Often neither pure CLI nor pure MCP is best.

<!-- src: audit-agentic-cli/references/mcp-vs-cli-decision.md#6.1 MCP Control Plane, CLI Execution Plane -->
### MCP control plane, CLI execution plane

| Plane | Owns |
|---|---|
| MCP (control) | auth, approval, tool discovery, tenant isolation |
| CLI (execution) | read-heavy operations, local transforms, batch processing, shell-native execution |

This is the right split when an operator surface already exists as a CLI but the agent surface needs governance.

<!-- src: audit-agentic-cli/references/mcp-vs-cli-decision.md#6.2 Skill + CLI -->
### Skill + CLI

Use a skill when the missing piece is not runtime capability but judgment and workflow. Examples:

- "For GitHub triage, prefer `gh --json` and summarize with `jq`."
- "For deploy validation, run these four commands in order and stop on this exit code."

That beats an MCP server whose only job is to explain an existing CLI.

<!-- src: audit-agentic-cli/references/mcp-vs-cli-decision.md#6.3 CLI First, MCP Fallback -->
### CLI first, MCP fallback

Works when most operations are stateless but a small subset is stateful or governed:

1. try the CLI first;
2. route stateful or approval-gated operations to MCP;
3. keep the boundary explicit in the skill or system instructions.

<!-- src: audit-agentic-cli/references/mcp-vs-cli-decision.md#8. Migration Paths -->
## Migration paths

| Current state | Move to | When |
|---|---|---|
| Raw shell commands with brittle parsing | Agent-ready CLI | The abstraction is right, but the contract is weak. |
| Good CLI plus repeated workflow mistakes | Skill + CLI | The runtime is fine; the agent needs better routing and examples. |
| CLI with growing auth and governance demands | MCP or MCP gateway | The problem is no longer just execution; it is custody and policy. |
| Large MCP server with thin endpoint wrappers | Smaller MCP, hybrid, or CLI | The server is carrying protocol tax without enough protocol value. |
| MCP that mostly wraps a local CLI | Skill + CLI, or MCP gateway with CLI backend | Keep only the part that adds auth, approval, or discovery value. |

<!-- src: audit-agentic-cli/references/mcp-vs-cli-decision.md#9. Decision Rules To Apply In This Skill -->
## Decision rules

1. Default to keeping the workflow in a CLI if the core problem is output quality, exit codes, auth ergonomics or non-interactive behavior.
2. Recommend MCP only when the requirements clearly justify protocol features: per-user auth, typed remote discovery, shared multi-client use or stateful sessions.
3. Recommend a skill when the problem is mainly workflow guidance rather than runtime access.
4. Recommend a hybrid when auth and governance pull toward MCP but the work itself still looks like cheap, deterministic command execution.
5. State explicitly whether the recommendation is based on documented facts, benchmark evidence or practitioner reports.
