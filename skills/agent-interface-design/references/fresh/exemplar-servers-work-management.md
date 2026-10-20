---
as_of: 2026-04
verify_before_citing: true
---

# Exemplar profiles: Linear, Notion, Atlassian Rovo, Asana V2

> Read when: you design an MCP server for a work-management or productivity suite (flattened GraphQL filters, hybrid AI-first tools, cross-product entities, OAuth without DCR). Overview: `exemplar-servers.md`.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Linear -->
## Linear

- **Source:** `linear.app/docs/mcp`; reverse-engineered tool dump at `blog.fiberplane.com/blog/mcp-server-analysis-linear/` (2025).
- **Surface:** 23 tools, remote-only: `list_issues`, `list_projects`, `list_teams`, `list_users`, `list_documents`, `list_cycles`, `list_comments`, `list_issue_labels`, `list_issue_statuses`, `list_project_labels`; `get_issue`, `get_project`, `get_team`, `get_user`, `get_document`, `get_issue_status`; `create_issue`, `create_project`, `create_comment`, `create_issue_label`; `update_issue`, `update_project`; `search_documentation`.
- **Naming / granularity:** `snake_case`; intent-consolidated, explicitly not a 1:1 GraphQL wrapper. Nested GraphQL filters collapsed into flat `assigneeId`, `teamId`, `stateId`. Magic value `"me"` accepted for assignee.
- **Schema:** strict validation (UUID cursors, hex colors). Enum values hard-coded in parameter descriptions (for example priority `0 = No priority, 1 = Urgent, 2 = High, 3 = Normal, 4 = Low`). See `mcp/schemas-*` on flat parameter shapes.
- **Response:** stringified JSON in `content[].text`; no `structuredContent`. Tool catalog measures 17.3k tokens after connect; context jumps roughly 61k to 78k.
- **Unique:** the `search_documentation` tool has no matching API endpoint: a deliberate knowledge-layer bolt-on. The clearest signal that Linear considers MCP a separate product surface, not an API mirror.
- **Auth / transport:** OAuth, hosted Streamable HTTP.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Notion — `makenotion/notion-mcp-server` + hosted -->
## Notion (`makenotion/notion-mcp-server` and hosted)

- **Source:** `notion.com/blog/notions-hosted-mcp-server-an-inside-look` (2026 post-mortem).
- **Surface:** v1 = 19 tools (1:1 from OpenAPI, auto-generated); v2 = 22 tools (hybrid, AI-first rewrites + wrappers for gap coverage).
- **Naming:** `kebab-case`, unusual: `query-data-source`, `retrieve-a-data-source`, `update-a-data-source`, `create-a-data-source`, `list-data-source-templates`, `move-page`, `retrieve-a-database`. Hosted v2 adds agentic tools: `create-pages`, `update-page`, `search`, `create-comment`.
- **Response:** "Notion-flavored Markdown" for page content, introduced because raw JSON blocks were too token-heavy.
- **Pipeline:** OpenAPI to Zod for schema generation; hand-written tools layered on top.
- **Auth / transport:** OAuth "one-click" shared public integration. Streamable HTTP primary + SSE fallback.
- **Unique tool:** `search` surfaces the Notion workspace plus 10+ connected apps through one entry point, a Deep-Research-style tool inside a productivity MCP.
- **Post-mortem claim (verbatim):** "1:1 API-to-tool mapping produced poor agent experiences, including high token use from hierarchical JSON block data." (Avoid 1.)

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Atlassian Rovo MCP Server -->
## Atlassian Rovo MCP Server

- **Source:** `support.atlassian.com/atlassian-rovo-mcp-server/docs/supported-tools/`. GA 2026-02-04.
- **Surface:** 54 tools: Jira (13), Confluence (11), JSM (4), Bitbucket Cloud (23), Rovo code/shared (4), Teamwork Graph (2 beta), Compass (12). The listed components sum to 69 (see Conflicts in `exemplar-servers.md`).
- **Naming:** `camelCase`, the major ecosystem outlier: `getJiraIssue`, `createConfluencePage`, `searchJiraIssuesUsingJql`.
- **Granularity:** hybrid. Per-operation for Jira/Confluence/JSM. Bitbucket uses nested dotted sub-action names: `bitbucketPullRequest.approve`, `bitbucketRepoContent.branch.get`, `bitbucketPipeline.step.log`: hierarchy inside a single tool name.
- **Response:** Confluence body delivered as Markdown.
- **Unique:** beta `fetch` + `search` universal tools Rovo-powered across products; `getTeamworkGraphContext` / `getTeamworkGraphObject` expose the cross-product entity graph.
- **Auth:** OAuth; users consent per AI client; admins allowlist clients.

<!-- src: audit-agentic-mcp/references/patterns/exemplar-servers.md#Asana V2 MCP -->
## Asana V2 MCP

- **Source:** `developers.asana.com/docs/integrating-with-asanas-mcp-server`. V1 shutdown 2026-05-11.
- **Dated claim:** the V1 sunset date 2026-05-11 had passed when this corpus was written (2026-10-20). Verify before citing; the V2 endpoint below is the one to use.
- **Endpoint:** `https://mcp.asana.com/v2/mcp` (no more `/sse`). Tool count not published; docs tell clients to call `tools/list`.
- **Auth:** OAuth 2.0 with a pre-registered app (`client_id` + `client_secret`). DCR NOT supported. Optional RFC 8707 `resource=https://mcp.asana.com/v2` param; `scope=default`; refresh tokens supported; 1 h access tokens.
- **Isolation quirk:** tokens issued for MCP apps only work with the MCP server, not with the REST API: deliberate surface isolation.
- **Common error:** "Invalid scope(s) requested" is caused by including the `scope` param at all.
- **Downstream impact:** Docker MCP Gateway (issue #479) is blocked on the no-DCR decision pending the V1 sunset (Avoid 5).
