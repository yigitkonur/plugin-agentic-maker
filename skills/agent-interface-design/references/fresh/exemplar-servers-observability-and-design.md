---
as_of: 2026-04
verify_before_citing: true
---

# Exemplar profiles: Sentry, Supabase, Figma

> Read when: you design an MCP server with tool groups chosen at consent time, prompt-injection wrapping of query results, annotations plus output schemas, or server-side repo introspection. Overview: `exemplar-servers.md`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Sentry — `getsentry/sentry-mcp` -->
## Sentry (`getsentry/sentry-mcp`)

- **Source:** `docs.sentry.io/ai/mcp/`.
- **Surface:** about 10-15 tools including `search_events`, `search_issues`, `use_sentry`. Tool groups (Issues/Errors/Projects/Seer/discovery) selectable at OAuth consent time.
- **Unique:** NL search tools require a caller-supplied `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` via `EMBEDDED_AGENT_PROVIDER`: an embedded LLM inside the MCP. `MCP_DISABLE_SKILLS=seer` disables cloud-only features. The Claude Code plugin registers a `sentry-mcp` subagent.
- **Auth / transport:** Cloud = OAuth Streamable HTTP at `mcp.sentry.dev/mcp`; device-code for stdio. Self-hosted = access token. Session cached at `~/.sentry/mcp.json`, scoped by org/project.
- **Response discipline:** the sister `build_sim` pattern returns only `warnings | errors | status | next-step hints`, median 2.1 KB vs raw xcodebuild logs.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Supabase — `supabase-community/supabase-mcp` -->
## Supabase (`supabase-community/supabase-mcp`)

- **Source:** `github.com/supabase-community/supabase-mcp`.
- **Surface:** 27 tools (README lists 32, feature-filtered), `snake_case`. Feature groups: `account`, `docs`, `database`, `debugging`, `development`, `functions`, `storage`, `branching`. Default disables `storage` "to reduce tool count."
- **Schema:** Zod v4 with both `parameters` AND `outputSchema` on every tool. Heavy use of MCP annotations: `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint` (Copy 1 in `exemplar-servers-copy-patterns.md`).
- **URL-query-param config:** hosted at `mcp.supabase.com/mcp` accepts `?project_ref=`, `?read_only=true`, `?features=database,docs`; no client restart needed to change scope (Copy 4).
- **Prompt-injection defense:** `execute_sql` wraps results in `<untrusted-data-${UUID}>...</untrusted-data-${UUID}>` with a generated UUID per call and an embedded instruction to ignore commands inside. Source: `packages/mcp-server-supabase/src/tools/database-operation-tools.ts` (Copy 2; `mcp/security/*`).
- **Deliberate `structuredContent` omission:** README notes "This server does not send `structuredContent`; Vercel AI SDK parses JSON from content text." (Disagreement 3.)
- **Client helper:** `createToolSchemas()` exposes the same feature/scope filter client-side for TS type safety.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Figma Dev Mode MCP -->
## Figma Dev Mode MCP

- **Source:** `developers.figma.com/docs/figma-mcp-server/tools-and-prompts/`; announcements `figma.com/blog/introducing-figma-mcp-server/` (2025-06-04 beta) and `figma.com/blog/design-systems-ai-mcp/` (2025-08-06).
- **Surface:** 15 tools (launched with 3), `snake_case`. Includes `generate_figma_design`, `get_design_context`, `get_variable_defs`, `get_code_connect_map`, `add_code_connect_map`, `get_screenshot`, `create_design_system_rules`, `get_metadata`, `get_figjam`, `generate_diagram`, `whoami`, `get_code_connect_suggestions`, `send_code_connect_mappings`, `use_figma`, `search_design_system`, `create_new_file`.
- **Unique:**
  - `generate_diagram` converts Mermaid syntax to FigJam: a reverse-bridge no other vendor replicates.
  - `create_design_system_rules` scans the caller's codebase and emits a rules file for agent guidance.
  - `use_figma` is a general create/edit/inspect tool.
  - `whoami` returns auth identity.
  - Docs explicitly mark tools "remote only" when hosted-only.
- **Response:** code tools configurable (React + Tailwind default); `get_metadata` returns sparse XML; `get_figjam` returns XML + screenshots.
- **Auth / transport:** Figma desktop app session; local stdio with remote tools mixed in.
- **Design thesis (verbatim from launch blog):** "Context > pixels; goal is alignment to design intent, not pixel-matching."
